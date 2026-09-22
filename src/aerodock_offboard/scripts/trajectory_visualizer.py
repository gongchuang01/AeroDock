#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Path
from visualization_msgs.msg import Marker, MarkerArray
from px4_msgs.msg import VehicleLocalPosition

class TrajectoryVisualizer(Node):
    def __init__(self):
        super().__init__("trajectory_visualizer")
        self.declare_parameter("waypoints", [0.0,0.0,3.0, 3.0,0.0,3.0, 3.0,3.0,3.0, 0.0,3.0,3.0, 0.0,0.0,3.0])
        values = self.get_parameter("waypoints").value
        self.waypoints = [values[i:i+3] for i in range(0, len(values), 3)]
        self.path = Path()
        self.path.header.frame_id = "map"
        self.last_point = None
        self.path_pub = self.create_publisher(Path, "/aerodock/trajectory", 10)
        self.marker_pub = self.create_publisher(MarkerArray, "/aerodock/waypoints", 10)
        self.create_subscription(VehicleLocalPosition, "/fmu/out/vehicle_local_position",
                                 self.on_position, qos_profile_sensor_data)
        self.create_timer(1.0, self.publish_markers)
        self.publish_markers()
        self.get_logger().info(f"Visualizing {len(self.waypoints)} waypoints")

    def on_position(self, msg):
        if not (msg.xy_valid and msg.z_valid):
            return
        # PX4 NED -> ROS ENU
        point = (float(msg.y), float(msg.x), float(-msg.z))
        if self.last_point and math.dist(point, self.last_point) < 0.05:
            return
        self.last_point = point
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"
        pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = point
        pose.pose.orientation.w = 1.0
        self.path.header.stamp = pose.header.stamp
        self.path.poses.append(pose)
        if len(self.path.poses) > 5000:
            self.path.poses = self.path.poses[-5000:]
        self.path_pub.publish(self.path)

    def publish_markers(self):
        now = self.get_clock().now().to_msg()
        result = MarkerArray()
        route = Marker()
        route.header.frame_id = "map"
        route.header.stamp = now
        route.ns = "route"
        route.id = 0
        route.type = Marker.LINE_STRIP
        route.action = Marker.ADD
        route.scale.x = 0.08
        route.color.r, route.color.g, route.color.b, route.color.a = 0.1, 0.75, 1.0, 1.0
        for north, east, altitude in self.waypoints:
            p = Point()
            p.x, p.y, p.z = east, north, altitude
            route.points.append(p)
        result.markers.append(route)

        for i, (north, east, altitude) in enumerate(self.waypoints):
            sphere = Marker()
            sphere.header.frame_id = "map"
            sphere.header.stamp = now
            sphere.ns = "waypoints"
            sphere.id = i + 1
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose.position.x, sphere.pose.position.y, sphere.pose.position.z = east, north, altitude
            sphere.pose.orientation.w = 1.0
            sphere.scale.x = sphere.scale.y = sphere.scale.z = 0.35
            sphere.color.r, sphere.color.g, sphere.color.b, sphere.color.a = 1.0, 0.45, 0.05, 1.0
            result.markers.append(sphere)

            label = Marker()
            label.header = sphere.header
            label.ns = "labels"
            label.id = 100 + i
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD
            label.pose.position.x, label.pose.position.y = east, north
            label.pose.position.z = altitude + 0.45
            label.pose.orientation.w = 1.0
            label.scale.z = 0.32
            label.color.r = label.color.g = label.color.b = label.color.a = 1.0
            label.text = f"WP{i+1}"
            result.markers.append(label)
        self.marker_pub.publish(result)

def main():
    rclpy.init()
    node = TrajectoryVisualizer()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
