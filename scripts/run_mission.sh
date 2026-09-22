#!/usr/bin/env bash
set -eo pipefail
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
source /opt/ros/humble/setup.bash
source "$AERODOCK_HOME/ros2_ws/install/px4_msgs/share/px4_msgs/local_setup.bash"
source "$AERODOCK_HOME/ros2_ws/install/aerodock_offboard/share/aerodock_offboard/local_setup.bash"
ros2 launch aerodock_offboard mission.launch.py
