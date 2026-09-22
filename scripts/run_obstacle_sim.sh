#!/usr/bin/env bash
set -eo pipefail
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
LOG_DIR="$AERODOCK_HOME/logs"
CMD_FILE="/tmp/aerodock-px4-obstacle-commands"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
export SVGA_VGPU10=0
mkdir -p "$LOG_DIR"
source /opt/ros/humble/setup.bash
: > "$CMD_FILE"
: > "$LOG_DIR/obstacle-sim.log"

if ! pgrep -f "MicroXRCEAgent udp4 -p 8888" >/dev/null; then
  nohup "$AERODOCK_HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" udp4 -p 8888 > "$LOG_DIR/xrce-runtime.log" 2>&1 &
fi

nohup setsid sh -c "tail -n 0 -f $CMD_FILE | env SVGA_VGPU10=0 HEADLESS=1 PX4_GZ_WORLD=walls make -C $AERODOCK_HOME/PX4-Autopilot px4_sitl gz_x500_lidar_2d" > "$LOG_DIR/obstacle-sim.log" 2>&1 &

for _ in $(seq 1 45); do
  grep -q "Startup script returned successfully" "$LOG_DIR/obstacle-sim.log" && break
  sleep 1
done
if ! grep -q "Startup script returned successfully" "$LOG_DIR/obstacle-sim.log"; then
  echo "Obstacle simulation failed. See $LOG_DIR/obstacle-sim.log" >&2
  exit 1
fi
echo "param set NAV_DLL_ACT 0" >> "$CMD_FILE"
LIDAR_TOPIC="/world/walls/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan"
nohup ros2 run ros_gz_bridge parameter_bridge "$LIDAR_TOPIC@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan" > "$LOG_DIR/lidar-bridge.log" 2>&1 &
echo $! > "$LOG_DIR/lidar-bridge.pid"
echo "Obstacle SITL ready: walls world + 2D lidar bridged to ROS 2."
