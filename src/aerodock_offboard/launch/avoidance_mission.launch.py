from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    share = get_package_share_directory("aerodock_offboard")
    return LaunchDescription([
        Node(package="aerodock_offboard", executable="waypoint_mission",
             name="waypoint_mission", output="screen",
             parameters=[os.path.join(share, "config", "waypoints.yaml")]),
        Node(package="aerodock_offboard", executable="local_avoidance.py",
             name="local_avoidance_planner", output="screen",
             parameters=[os.path.join(share, "config", "local_avoidance.yaml")]),
    ])
