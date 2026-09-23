import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory("aerodock_offboard")
    mission = Node(
        package="aerodock_offboard",
        executable="waypoint_mission",
        name="waypoint_mission",
        output="screen",
        parameters=[
            os.path.join(share, "config", "avoidance_waypoints.yaml"),
            {"mission_timeout_seconds": 180.0},
        ],
    )
    planner = Node(
        package="aerodock_offboard",
        executable="local_avoidance.py",
        name="local_avoidance_planner",
        output="screen",
        parameters=[os.path.join(share, "config", "local_avoidance.yaml")],
    )
    stop_when_mission_finishes = RegisterEventHandler(
        OnProcessExit(
            target_action=mission,
            on_exit=[EmitEvent(event=Shutdown(reason="waypoint mission finished"))],
        )
    )
    return LaunchDescription([mission, planner, stop_when_mission_finishes])
