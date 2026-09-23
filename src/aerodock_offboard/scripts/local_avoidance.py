#!/usr/bin/env python3
import math
import statistics
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PointStamped
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from px4_msgs.msg import VehicleLocalPosition, VehicleStatus

SCAN_TOPIC = "/world/aerodock_obstacles/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan"

class LocalAvoidancePlanner(Node):
    def __init__(self):
        super().__init__("local_avoidance_planner")
        self.declare_parameter("trigger_distance_m", 2.0)
        self.declare_parameter("clear_distance_m", 2.6)
        self.declare_parameter("forward_offset_m", 1.5)
        self.declare_parameter("lateral_offset_m", 2.0)
        self.declare_parameter("confirm_scans", 3)
        self.declare_parameter("require_armed", True)
        self.declare_parameter("min_flight_altitude_m", 2.0)
        self.declare_parameter("sensor_yaw_offset_deg", 90.0)
        self.trigger_distance = float(self.get_parameter("trigger_distance_m").value)
        self.clear_distance = float(self.get_parameter("clear_distance_m").value)
        self.forward_offset = float(self.get_parameter("forward_offset_m").value)
        self.lateral_offset = float(self.get_parameter("lateral_offset_m").value)
        self.confirm_scans = int(self.get_parameter("confirm_scans").value)
        self.require_armed = bool(self.get_parameter("require_armed").value)
        self.min_flight_altitude = float(self.get_parameter("min_flight_altitude_m").value)
        self.sensor_yaw_offset = math.radians(
            float(self.get_parameter("sensor_yaw_offset_deg").value))

        self.position_valid = False
        self.north = self.east = self.altitude = self.heading = 0.0
        self.block_count = 0
        self.clear_count = 0
        self.active = False
        self.armed = False
        self.last_detour_ns = 0

        self.detour_pub = self.create_publisher(PointStamped, "/aerodock/avoidance/detour", 10)
        self.decision_pub = self.create_publisher(String, "/aerodock/avoidance/decision", 10)
        self.create_subscription(LaserScan, SCAN_TOPIC, self.on_scan, qos_profile_sensor_data)
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position",
                                 self.on_position, qos_profile_sensor_data)
        self.create_subscription(VehicleStatus, "/fmu/out/vehicle_status_v1",
                                 self.on_status, qos_profile_sensor_data)
        self.get_logger().info(
            f"Local planner ready: trigger={self.trigger_distance:.1f} m, "
            f"detour=({self.forward_offset:.1f} m forward, {self.lateral_offset:.1f} m lateral)")

    def on_status(self, msg):
        self.armed = msg.arming_state == VehicleStatus.ARMING_STATE_ARMED

    def on_position(self, msg):
        if msg.xy_valid and msg.z_valid:
            self.north = float(msg.x)
            self.east = float(msg.y)
            self.altitude = float(-msg.z)
            self.heading = float(msg.heading)
            self.position_valid = True

    @staticmethod
    def sector_values(msg, low_deg, high_deg):
        low = math.radians(low_deg)
        high = math.radians(high_deg)
        values = []
        angle = msg.angle_min
        for distance in msg.ranges:
            if low <= angle <= high and math.isfinite(distance):
                if msg.range_min <= distance <= msg.range_max:
                    values.append(float(distance))
            angle += msg.angle_increment
        return values

    @staticmethod
    def clearance(values, range_max):
        if not values:
            return float(range_max)
        return statistics.median(values)

    def publish_decision(self, text):
        msg = String()
        msg.data = text
        self.decision_pub.publish(msg)

    def on_scan(self, msg):
        front_values = self.sector_values(msg, -25.0, 25.0)
        left_values = self.sector_values(msg, 25.0, 100.0)
        right_values = self.sector_values(msg, -100.0, -25.0)
        front = min(front_values) if front_values else float("inf")

        if front < self.trigger_distance:
            self.block_count += 1
            self.clear_count = 0
        elif front > self.clear_distance:
            self.clear_count += 1
            self.block_count = 0

        now_ns = self.get_clock().now().nanoseconds
        if not self.active and self.block_count >= self.confirm_scans:
            self.active = True
            self.make_detour(msg, front, left_values, right_values)
        elif (self.active and front < self.trigger_distance and
              now_ns - self.last_detour_ns >= 1_000_000_000):
            self.make_detour(msg, front, left_values, right_values)
        elif self.active and self.clear_count >= self.confirm_scans:
            self.active = False
            self.publish_decision("CLEAR")
            self.get_logger().info("Path clear; resume original route")

    def make_detour(self, msg, front, left_values, right_values):
        self.last_detour_ns = self.get_clock().now().nanoseconds
        if self.require_armed and not self.armed:
            self.publish_decision("BLOCKED_VEHICLE_DISARMED")
            self.get_logger().warn("Obstacle detected while vehicle is disarmed; no detour published")
            return

        if not self.position_valid:
            self.publish_decision("BLOCKED_WAITING_FOR_POSITION")
            self.get_logger().warn("Obstacle detected but local position is not valid")
            return

        if self.altitude < self.min_flight_altitude:
            self.active = False
            self.block_count = 0
            self.publish_decision("WAITING_FOR_SAFE_ALTITUDE")
            self.get_logger().info(
                f"Obstacle ignored during takeoff: altitude={self.altitude:.2f} m, "
                f"minimum={self.min_flight_altitude:.2f} m")
            return

        left = self.clearance(left_values, msg.range_max)
        right = self.clearance(right_values, msg.range_max)
        choose_left = left >= right
        lateral_right = -self.lateral_offset if choose_left else self.lateral_offset

        # Sensor forward/right offset converted to PX4 local NED north/east.
        sensor_heading = self.heading + self.sensor_yaw_offset
        target_north = (self.north + self.forward_offset * math.cos(sensor_heading)
                        - lateral_right * math.sin(sensor_heading))
        target_east = (self.east + self.forward_offset * math.sin(sensor_heading)
                       + lateral_right * math.cos(sensor_heading))

        point = PointStamped()
        point.header.stamp = self.get_clock().now().to_msg()
        point.header.frame_id = "px4_ned_altitude"
        point.point.x = target_north
        point.point.y = target_east
        point.point.z = self.altitude
        self.detour_pub.publish(point)
        self.last_detour_ns = self.get_clock().now().nanoseconds

        side = "LEFT" if choose_left else "RIGHT"
        decision = (f"DETOUR_{side} front={front:.2f}m "
                    f"left={left:.2f}m right={right:.2f}m "
                    f"target=({target_north:.2f},{target_east:.2f},{self.altitude:.2f})")
        self.publish_decision(decision)
        self.get_logger().warn(decision)

def main():
    rclpy.init()
    node = LocalAvoidancePlanner()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()
