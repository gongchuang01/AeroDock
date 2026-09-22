#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32
from px4_msgs.msg import VehicleCommand, VehicleStatus

SCAN_TOPIC = "/world/walls/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan"

class ObstacleSafety(Node):
    def __init__(self):
        super().__init__("obstacle_safety")
        self.declare_parameter("stop_distance_m", 1.5)
        self.declare_parameter("forward_sector_deg", 60.0)
        self.declare_parameter("confirm_scans", 3)
        self.declare_parameter("action", "land")
        self.stop_distance = float(self.get_parameter("stop_distance_m").value)
        self.half_sector = math.radians(float(self.get_parameter("forward_sector_deg").value) / 2.0)
        self.confirm_scans = int(self.get_parameter("confirm_scans").value)
        self.action = str(self.get_parameter("action").value)
        self.close_count = 0
        self.blocked = False
        self.armed = False
        self.land_sent = False
        self.scan_count = 0

        self.distance_pub = self.create_publisher(Float32, "/aerodock/obstacle/min_distance", 10)
        self.blocked_pub = self.create_publisher(Bool, "/aerodock/obstacle/blocked", 10)
        self.command_pub = self.create_publisher(VehicleCommand, "/fmu/in/vehicle_command", 10)
        self.create_subscription(LaserScan, SCAN_TOPIC, self.on_scan, qos_profile_sensor_data)
        self.create_subscription(VehicleStatus, "/fmu/out/vehicle_status_v1",
                                 self.on_status, qos_profile_sensor_data)
        self.get_logger().info(
            f"Obstacle safety active: threshold={self.stop_distance:.2f} m, "
            f"sector={math.degrees(self.half_sector) * 2:.0f} deg, action={self.action}")

    def on_status(self, msg):
        self.armed = msg.arming_state == VehicleStatus.ARMING_STATE_ARMED
        if not self.armed:
            self.land_sent = False

    def on_scan(self, msg):
        valid = []
        angle = msg.angle_min
        for distance in msg.ranges:
            if -self.half_sector <= angle <= self.half_sector:
                if math.isfinite(distance) and msg.range_min <= distance <= msg.range_max:
                    valid.append(float(distance))
            angle += msg.angle_increment
        minimum = min(valid) if valid else float("inf")
        self.scan_count += 1

        distance_msg = Float32()
        distance_msg.data = minimum
        self.distance_pub.publish(distance_msg)

        if minimum < self.stop_distance:
            self.close_count += 1
        else:
            self.close_count = 0
        new_blocked = self.close_count >= self.confirm_scans

        blocked_msg = Bool()
        blocked_msg.data = new_blocked
        self.blocked_pub.publish(blocked_msg)

        if new_blocked != self.blocked:
            self.blocked = new_blocked
            if self.blocked:
                self.get_logger().warn(f"Obstacle confirmed at {minimum:.2f} m")
            else:
                self.get_logger().info("Forward path clear")

        if self.scan_count % 35 == 0:
            text = "no return" if not math.isfinite(minimum) else f"{minimum:.2f} m"
            self.get_logger().info(f"Front minimum distance: {text}")

        if self.blocked and self.armed and self.action == "land" and not self.land_sent:
            self.send_land()
            self.land_sent = True
            self.get_logger().error("Safety action: PX4 landing command sent")

    def send_land(self):
        msg = VehicleCommand()
        msg.timestamp = int(self.get_clock().now().nanoseconds / 1000)
        msg.command = VehicleCommand.VEHICLE_CMD_NAV_LAND
        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.from_external = True
        self.command_pub.publish(msg)

def main():
    rclpy.init()
    node = ObstacleSafety()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
