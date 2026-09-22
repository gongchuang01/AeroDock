#!/usr/bin/env bash
set -eo pipefail
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
source /opt/ros/humble/setup.bash
source "$AERODOCK_HOME/ros2_ws/install/px4_msgs/share/px4_msgs/local_setup.bash"
source "$AERODOCK_HOME/ros2_ws/install/aerodock_offboard/share/aerodock_offboard/local_setup.bash"
nohup ros2 launch aerodock_offboard visualization.launch.py > "$AERODOCK_HOME/logs/visualization.log" 2>&1 &
echo $! > "$AERODOCK_HOME/logs/visualization.pid"
echo "RViz2 is opening on the Ubuntu desktop."
