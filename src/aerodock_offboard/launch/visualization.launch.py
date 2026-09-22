from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    share = get_package_share_directory("aerodock_offboard")
    return LaunchDescription([
        Node(package="aerodock_offboard", executable="trajectory_visualizer.py",
             name="trajectory_visualizer", output="screen",
             parameters=[os.path.join(share, "config", "waypoints.yaml")]),
        Node(package="rviz2", executable="rviz2", name="rviz2", output="screen",
             arguments=["-d", os.path.join(share, "rviz", "aerodock.rviz")]),
    ])
