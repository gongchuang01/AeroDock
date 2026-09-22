from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    share = get_package_share_directory("aerodock_offboard")
    return LaunchDescription([
        Node(package="aerodock_offboard", executable="obstacle_safety.py",
             name="obstacle_safety", output="screen",
             parameters=[os.path.join(share, "config", "obstacle_safety.yaml")])
    ])
