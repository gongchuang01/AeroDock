from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("aerodock_offboard"), "config", "mission.yaml"
    )
    return LaunchDescription([
        Node(
            package="aerodock_offboard",
            executable="offboard_mission",
            name="offboard_mission",
            output="screen",
            parameters=[config],
        )
    ])
