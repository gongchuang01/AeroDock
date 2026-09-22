#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/qos.hpp"
#include "geometry_msgs/msg/point_stamped.hpp"
#include "px4_msgs/msg/offboard_control_mode.hpp"
#include "px4_msgs/msg/trajectory_setpoint.hpp"
#include "px4_msgs/msg/vehicle_command.hpp"
#include "px4_msgs/msg/vehicle_local_position.hpp"
#include "px4_msgs/msg/vehicle_status.hpp"

using namespace std::chrono_literals;
struct Waypoint { float x; float y; float altitude; };

class WaypointMission : public rclcpp::Node {
public:
  WaypointMission() : Node("waypoint_mission") {
    declare_parameter("waypoints", std::vector<double>{
      0,0,3, 3,0,3, 3,3,3, 0,3,3, 0,0,3});
    declare_parameter("acceptance_radius_m", 0.45);
    declare_parameter("hold_seconds", 1.5);
    declare_parameter("mission_timeout_seconds", 90.0);
    declare_parameter("detour_timeout_seconds", 20.0);
    declare_parameter("enable_detours", true);
    declare_parameter("log_path", std::string("/home/gc/aerodock/logs/waypoint-flight.csv"));

    auto values = get_parameter("waypoints").as_double_array();
    if (values.empty() || values.size() % 3 != 0) {
      throw std::runtime_error("waypoints must be a non-empty [x,y,altitude,...] array");
    }
    for (size_t i = 0; i < values.size(); i += 3) {
      waypoints_.push_back({static_cast<float>(values[i]),
                            static_cast<float>(values[i + 1]),
                            static_cast<float>(values[i + 2])});
    }
    radius_ = get_parameter("acceptance_radius_m").as_double();
    hold_seconds_ = get_parameter("hold_seconds").as_double();
    timeout_seconds_ = get_parameter("mission_timeout_seconds").as_double();
    detour_timeout_seconds_ = get_parameter("detour_timeout_seconds").as_double();
    enable_detours_ = get_parameter("enable_detours").as_bool();

    csv_.open(get_parameter("log_path").as_string(), std::ios::trunc);
    csv_ << "time_s,state,waypoint,x_m,y_m,altitude_m,target_x_m,target_y_m,target_altitude_m,error_m\n";

    mode_pub_ = create_publisher<px4_msgs::msg::OffboardControlMode>("/fmu/in/offboard_control_mode", 10);
    setpoint_pub_ = create_publisher<px4_msgs::msg::TrajectorySetpoint>("/fmu/in/trajectory_setpoint", 10);
    command_pub_ = create_publisher<px4_msgs::msg::VehicleCommand>("/fmu/in/vehicle_command", 10);

    auto qos = rclcpp::SensorDataQoS();
    status_sub_ = create_subscription<px4_msgs::msg::VehicleStatus>(
      "/fmu/out/vehicle_status_v1", qos,
      [this](px4_msgs::msg::VehicleStatus::UniquePtr m) {
        armed_ = m->arming_state == px4_msgs::msg::VehicleStatus::ARMING_STATE_ARMED;
        offboard_ = m->nav_state == px4_msgs::msg::VehicleStatus::NAVIGATION_STATE_OFFBOARD;
      });
    position_sub_ = create_subscription<px4_msgs::msg::VehicleLocalPosition>(
      "/fmu/out/vehicle_local_position", qos,
      [this](px4_msgs::msg::VehicleLocalPosition::UniquePtr m) {
        if (m->xy_valid && m->z_valid) {
          x_ = m->x; y_ = m->y; altitude_ = -m->z; position_valid_ = true;
        }
      });
    detour_sub_ = create_subscription<geometry_msgs::msg::PointStamped>(
      "/aerodock/avoidance/detour", 10,
      [this](geometry_msgs::msg::PointStamped::UniquePtr m) {
        if (!enable_detours_ || state_ != State::NAVIGATING || !armed_) return;
        if (m->header.frame_id != "px4_ned_altitude") {
          RCLCPP_WARN(get_logger(), "Ignoring detour with frame '%s'", m->header.frame_id.c_str());
          return;
        }
        detour_ = {static_cast<float>(m->point.x), static_cast<float>(m->point.y),
                   static_cast<float>(m->point.z)};
        detour_active_ = true;
        detour_start_ = now();
        inside_since_ = zero_time();
        RCLCPP_WARN(get_logger(), "Detour accepted: N %.2f E %.2f alt %.2f",
                    detour_.x, detour_.y, detour_.altitude);
      });

    mission_start_ = now();
    state_start_ = now();
    last_command_ = now();
    detour_start_ = now();
    timer_ = create_wall_timer(100ms, std::bind(&WaypointMission::tick, this));
    RCLCPP_INFO(get_logger(), "Loaded %zu waypoints; detours %s",
                waypoints_.size(), enable_detours_ ? "enabled" : "disabled");
  }

private:
  enum class State { PRESTREAM, WAIT_ARMED, NAVIGATING, LANDING, DONE };

  rclcpp::Time zero_time() { return rclcpp::Time(0, 0, get_clock()->get_clock_type()); }
  uint64_t timestamp_us() { return static_cast<uint64_t>(now().nanoseconds() / 1000); }
  double state_seconds() { return (now() - state_start_).seconds(); }
  double mission_seconds() { return (now() - mission_start_).seconds(); }
  const Waypoint &target() const { return detour_active_ ? detour_ : waypoints_[waypoint_index_]; }

  const char *state_name() const {
    if (state_ == State::NAVIGATING && detour_active_) return "DETOUR";
    switch (state_) {
      case State::PRESTREAM: return "PRESTREAM";
      case State::WAIT_ARMED: return "WAIT_ARMED";
      case State::NAVIGATING: return "NAVIGATING";
      case State::LANDING: return "LANDING";
      default: return "DONE";
    }
  }

  double error_to_target() const {
    const auto &w = target();
    return std::sqrt(std::pow(x_ - w.x, 2) + std::pow(y_ - w.y, 2) +
                     std::pow(altitude_ - w.altitude, 2));
  }

  void publish_target() {
    px4_msgs::msg::OffboardControlMode mode{};
    mode.timestamp = timestamp_us();
    mode.position = true;
    mode_pub_->publish(mode);
    const auto &w = target();
    px4_msgs::msg::TrajectorySetpoint setpoint{};
    setpoint.timestamp = timestamp_us();
    setpoint.position = {w.x, w.y, -w.altitude};
    setpoint.yaw = 0.0F;
    setpoint_pub_->publish(setpoint);
  }

  void command(uint32_t id, float p1 = 0, float p2 = 0) {
    px4_msgs::msg::VehicleCommand m{};
    m.timestamp = timestamp_us();
    m.param1 = p1; m.param2 = p2; m.command = static_cast<uint16_t>(id);
    m.target_system = 1; m.target_component = 1;
    m.source_system = 1; m.source_component = 1; m.from_external = true;
    command_pub_->publish(m);
  }

  void transition(State next, const std::string &message) {
    state_ = next; state_start_ = now(); inside_since_ = zero_time();
    RCLCPP_INFO(get_logger(), "%s", message.c_str());
  }

  void land(const std::string &reason) {
    command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
    last_command_ = now();
    transition(State::LANDING, reason);
  }

  void record() {
    if (!position_valid_ || ++log_counter_ % 5 != 0) return;
    const auto &w = target();
    csv_ << mission_seconds() << ',' << state_name() << ',' << waypoint_index_
         << ',' << x_ << ',' << y_ << ',' << altitude_
         << ',' << w.x << ',' << w.y << ',' << w.altitude
         << ',' << error_to_target() << '\n';
    csv_.flush();
  }

  void tick() {
    if (state_ == State::DONE) return;
    record();
    if (mission_seconds() > timeout_seconds_ && state_ != State::LANDING) {
      land("Mission timeout; landing"); return;
    }
    if (detour_active_ && (now() - detour_start_).seconds() > detour_timeout_seconds_) {
      land("Detour timeout; landing"); return;
    }

    if (state_ == State::PRESTREAM) {
      publish_target();
      if (++setpoint_count_ >= 20) {
        command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1, 6);
        command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1);
        last_command_ = now();
        transition(State::WAIT_ARMED, "Offboard requested; arming");
      }
      return;
    }

    if (state_ == State::WAIT_ARMED) {
      publish_target();
      if (armed_ && offboard_) {
        transition(State::NAVIGATING, "Armed; navigating to waypoint 1");
      } else if ((now() - last_command_).seconds() > 1) {
        command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1, 6);
        command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1);
        last_command_ = now();
      }
      if (state_seconds() > 12) land("Arming timeout; landing");
      return;
    }

    if (state_ == State::NAVIGATING) {
      publish_target();
      if (!armed_ || !offboard_) { land("Flight state lost; landing"); return; }
      if (position_valid_ && error_to_target() <= radius_) {
        if (inside_since_.nanoseconds() == 0) {
          inside_since_ = now();
          if (detour_active_) {
            RCLCPP_INFO(get_logger(), "Detour reached, error %.2f m", error_to_target());
          } else {
            RCLCPP_INFO(get_logger(), "Waypoint %zu reached, error %.2f m",
                        waypoint_index_ + 1, error_to_target());
          }
        }
        if ((now() - inside_since_).seconds() >= hold_seconds_) {
          if (detour_active_) {
            detour_active_ = false;
            inside_since_ = zero_time();
            RCLCPP_INFO(get_logger(), "Detour complete; resuming waypoint %zu", waypoint_index_ + 1);
          } else if (++waypoint_index_ >= waypoints_.size()) {
            waypoint_index_ = waypoints_.size() - 1;
            land("Route complete; landing");
          } else {
            inside_since_ = zero_time();
            RCLCPP_INFO(get_logger(), "Proceeding to waypoint %zu", waypoint_index_ + 1);
          }
        }
      } else {
        inside_since_ = zero_time();
      }
      return;
    }

    if (state_ == State::LANDING) {
      if (!armed_) {
        transition(State::DONE, "Landed and disarmed; waypoint mission complete");
        csv_.close(); rclcpp::shutdown();
      } else if ((now() - last_command_).seconds() > 2) {
        command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
        last_command_ = now();
      }
    }
  }

  State state_{State::PRESTREAM};
  std::vector<Waypoint> waypoints_;
  Waypoint detour_{0, 0, 0};
  size_t waypoint_index_{0};
  int setpoint_count_{0}, log_counter_{0};
  bool armed_{false}, offboard_{false}, position_valid_{false};
  bool detour_active_{false}, enable_detours_{true};
  float x_{0}, y_{0}, altitude_{0};
  double radius_{0.45}, hold_seconds_{1.5}, timeout_seconds_{90};
  double detour_timeout_seconds_{20};
  rclcpp::Time mission_start_, state_start_, last_command_, detour_start_;
  rclcpp::Time inside_since_{0, 0, RCL_ROS_TIME};
  std::ofstream csv_;
  rclcpp::Publisher<px4_msgs::msg::OffboardControlMode>::SharedPtr mode_pub_;
  rclcpp::Publisher<px4_msgs::msg::TrajectorySetpoint>::SharedPtr setpoint_pub_;
  rclcpp::Publisher<px4_msgs::msg::VehicleCommand>::SharedPtr command_pub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleStatus>::SharedPtr status_sub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleLocalPosition>::SharedPtr position_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PointStamped>::SharedPtr detour_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<WaypointMission>());
  rclcpp::shutdown();
  return 0;
}
