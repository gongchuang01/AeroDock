#include <chrono>
#include <cstdint>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/qos.hpp"
#include "px4_msgs/msg/offboard_control_mode.hpp"
#include "px4_msgs/msg/trajectory_setpoint.hpp"
#include "px4_msgs/msg/vehicle_command.hpp"
#include "px4_msgs/msg/vehicle_local_position.hpp"
#include "px4_msgs/msg/vehicle_status.hpp"

using namespace std::chrono_literals;

class OffboardMission : public rclcpp::Node {
public:
  OffboardMission() : Node("offboard_mission") {
    declare_parameter("takeoff_height_m", 3.0);
    declare_parameter("hover_seconds", 10.0);
    takeoff_height_ = get_parameter("takeoff_height_m").as_double();
    hover_seconds_ = get_parameter("hover_seconds").as_double();

    offboard_pub_ = create_publisher<px4_msgs::msg::OffboardControlMode>(
      "/fmu/in/offboard_control_mode", 10);
    setpoint_pub_ = create_publisher<px4_msgs::msg::TrajectorySetpoint>(
      "/fmu/in/trajectory_setpoint", 10);
    command_pub_ = create_publisher<px4_msgs::msg::VehicleCommand>(
      "/fmu/in/vehicle_command", 10);

    auto qos = rclcpp::SensorDataQoS();
    status_sub_ = create_subscription<px4_msgs::msg::VehicleStatus>(
      "/fmu/out/vehicle_status_v1", qos,
      [this](px4_msgs::msg::VehicleStatus::UniquePtr msg) {
        armed_ = msg->arming_state == px4_msgs::msg::VehicleStatus::ARMING_STATE_ARMED;
        offboard_ = msg->nav_state == px4_msgs::msg::VehicleStatus::NAVIGATION_STATE_OFFBOARD;
      });
    position_sub_ = create_subscription<px4_msgs::msg::VehicleLocalPosition>(
      "/fmu/out/vehicle_local_position", qos,
      [this](px4_msgs::msg::VehicleLocalPosition::UniquePtr msg) {
        if (msg->z_valid) {
          altitude_ = -msg->z;
          position_valid_ = true;
        }
      });

    mission_start_ = now();
    state_start_ = now();
    last_command_time_ = now();
    timer_ = create_wall_timer(100ms, std::bind(&OffboardMission::tick, this));
    RCLCPP_INFO(get_logger(), "Mission ready: takeoff %.1f m, hover %.1f s",
                takeoff_height_, hover_seconds_);
  }

private:
  enum class State { PRESTREAM, WAIT_ARMED, FLYING, LANDING, DONE };

  uint64_t timestamp_us() {
    return static_cast<uint64_t>(get_clock()->now().nanoseconds() / 1000);
  }

  void publish_offboard_setpoint() {
    px4_msgs::msg::OffboardControlMode mode{};
    mode.timestamp = timestamp_us();
    mode.position = true;
    offboard_pub_->publish(mode);

    px4_msgs::msg::TrajectorySetpoint setpoint{};
    setpoint.timestamp = timestamp_us();
    setpoint.position = {0.0F, 0.0F, static_cast<float>(-takeoff_height_)};
    setpoint.yaw = 0.0F;
    setpoint_pub_->publish(setpoint);
  }

  void send_command(uint32_t command, float param1 = 0.0F, float param2 = 0.0F) {
    px4_msgs::msg::VehicleCommand msg{};
    msg.timestamp = timestamp_us();
    msg.param1 = param1;
    msg.param2 = param2;
    msg.command = static_cast<uint16_t>(command);
    msg.target_system = 1;
    msg.target_component = 1;
    msg.source_system = 1;
    msg.source_component = 1;
    msg.from_external = true;
    command_pub_->publish(msg);
  }

  void change_state(State next, const std::string &reason) {
    state_ = next;
    state_start_ = now();
    RCLCPP_INFO(get_logger(), "%s", reason.c_str());
  }

  double state_seconds() { return (now() - state_start_).seconds(); }
  double mission_seconds() { return (now() - mission_start_).seconds(); }

  void tick() {
    if (state_ == State::DONE) return;

    if (mission_seconds() > 45.0 && state_ != State::LANDING) {
      send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
      change_state(State::LANDING, "Safety timeout reached; landing");
      return;
    }

    if (state_ == State::PRESTREAM) {
      publish_offboard_setpoint();
      if (++setpoint_count_ >= 20) {
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1.0F, 6.0F);
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0F);
        last_command_time_ = now();
        change_state(State::WAIT_ARMED, "Offboard requested; arming");
      }
      return;
    }

    if (state_ == State::WAIT_ARMED) {
      publish_offboard_setpoint();
      if (armed_ && offboard_) {
        change_state(State::FLYING, "Armed in Offboard; climbing to setpoint");
      } else if ((now() - last_command_time_).seconds() > 1.0) {
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_DO_SET_MODE, 1.0F, 6.0F);
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_COMPONENT_ARM_DISARM, 1.0F);
        last_command_time_ = now();
      }
      if (state_seconds() > 12.0) {
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
        change_state(State::LANDING, "Could not arm in 12 s; landing command sent");
      }
      return;
    }

    if (state_ == State::FLYING) {
      publish_offboard_setpoint();
      if (state_seconds() >= hover_seconds_) {
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
        last_command_time_ = now();
        change_state(State::LANDING, "Hover complete; landing");
      } else if (++setpoint_count_ % 20 == 0 && position_valid_) {
        RCLCPP_INFO(get_logger(), "Flying: altitude %.2f m, %.1f s remaining",
                    altitude_, hover_seconds_ - state_seconds());
      }
      return;
    }

    if (state_ == State::LANDING) {
      if (!armed_) {
        change_state(State::DONE, "Landed and disarmed; mission complete");
        rclcpp::shutdown();
      } else if ((now() - last_command_time_).seconds() > 2.0) {
        send_command(px4_msgs::msg::VehicleCommand::VEHICLE_CMD_NAV_LAND);
        last_command_time_ = now();
      }
    }
  }

  State state_{State::PRESTREAM};
  int setpoint_count_{0};
  bool armed_{false};
  bool offboard_{false};
  bool position_valid_{false};
  double altitude_{0.0};
  double takeoff_height_{3.0};
  double hover_seconds_{10.0};
  rclcpp::Time mission_start_;
  rclcpp::Time state_start_;
  rclcpp::Time last_command_time_;

  rclcpp::Publisher<px4_msgs::msg::OffboardControlMode>::SharedPtr offboard_pub_;
  rclcpp::Publisher<px4_msgs::msg::TrajectorySetpoint>::SharedPtr setpoint_pub_;
  rclcpp::Publisher<px4_msgs::msg::VehicleCommand>::SharedPtr command_pub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleStatus>::SharedPtr status_sub_;
  rclcpp::Subscription<px4_msgs::msg::VehicleLocalPosition>::SharedPtr position_sub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<OffboardMission>());
  rclcpp::shutdown();
  return 0;
}
