#!/usr/bin/env bash
set -eo pipefail

AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
LOG_DIR="$AERODOCK_HOME/logs"
CMD_FILE="/tmp/aerodock-px4-obstacle-commands"
RENDER_MODE="${AERODOCK_RENDER_MODE:-headless}"
LIDAR_SAMPLES="${AERODOCK_LIDAR_SAMPLES:-90}"
LIDAR_UPDATE_RATE="${AERODOCK_LIDAR_UPDATE_RATE:-5}"
LIDAR_MODEL="$AERODOCK_HOME/PX4-Autopilot/Tools/simulation/gz/models/lidar_2d_v2/model.sdf"

mkdir -p "$LOG_DIR"
ln -sfn "$AERODOCK_HOME/AeroDock/simulation/worlds/aerodock_obstacles.sdf" \
  "$AERODOCK_HOME/PX4-Autopilot/Tools/simulation/gz/worlds/aerodock_obstacles.sdf"

if [[ -f "$LIDAR_MODEL" ]]; then
  sed -Ei "s#<samples>[0-9]+</samples>#<samples>$LIDAR_SAMPLES</samples>#; s#<update_rate>[0-9.]+</update_rate>#<update_rate>$LIDAR_UPDATE_RATE</update_rate>#" "$LIDAR_MODEL"
else
  echo "Lidar model not found: $LIDAR_MODEL" >&2
  exit 1
fi

source /opt/ros/humble/setup.bash
: > "$CMD_FILE"
: > "$LOG_DIR/obstacle-sim.log"

if ! pgrep -f "MicroXRCEAgent udp4 -p 8888" >/dev/null; then
  nohup "$AERODOCK_HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" udp4 -p 8888     > "$LOG_DIR/xrce-runtime.log" 2>&1 &
fi

case "$RENDER_MODE" in
  headless)
    RENDER_ENV="env LIBGL_ALWAYS_SOFTWARE=1 SVGA_VGPU10=0 HEADLESS=1"
    ;;
  vmware-gui)
    : "${DISPLAY:?Set DISPLAY to the active Xwayland display}"
    : "${XAUTHORITY:?Set XAUTHORITY to a readable Xwayland authority file}"
    export DISPLAY XAUTHORITY
    export QT_X11_NO_MITSHM=1
    RENDER_ENV="env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY QT_X11_NO_MITSHM=1"
    ;;
  *)
    echo "Unknown AERODOCK_RENDER_MODE '$RENDER_MODE' (use headless or vmware-gui)" >&2
    exit 1
    ;;
esac

nohup setsid sh -c "tail -n 0 -f $CMD_FILE | $RENDER_ENV PX4_GZ_WORLD=aerodock_obstacles PX4_GZ_MODEL_POSE=0,0,0.5 make -C $AERODOCK_HOME/PX4-Autopilot px4_sitl gz_x500_lidar_2d" > "$LOG_DIR/obstacle-sim.log" 2>&1 &

for _ in $(seq 1 45); do
  grep -q "Startup script returned successfully" "$LOG_DIR/obstacle-sim.log" && break
  sleep 1
done
if ! grep -q "Startup script returned successfully" "$LOG_DIR/obstacle-sim.log"; then
  echo "Obstacle simulation failed. See $LOG_DIR/obstacle-sim.log" >&2
  exit 1
fi

echo "param set NAV_DLL_ACT 0" >> "$CMD_FILE"
for _ in $(seq 1 60); do
  grep -q "Ready for takeoff" "$LOG_DIR/obstacle-sim.log" && break
  sleep 1
done
if ! grep -q "Ready for takeoff" "$LOG_DIR/obstacle-sim.log"; then
  echo "PX4 estimator did not become ready. See $LOG_DIR/obstacle-sim.log" >&2
  exit 1
fi

LIDAR_TOPIC="/world/aerodock_obstacles/model/x500_lidar_2d_0/link/link/sensor/lidar_2d_v2/scan"
nohup ros2 run ros_gz_bridge parameter_bridge "$LIDAR_TOPIC@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan" > "$LOG_DIR/lidar-bridge.log" 2>&1 &
echo $! > "$LOG_DIR/lidar-bridge.pid"
echo "Obstacle SITL ready ($RENDER_MODE, lidar: $LIDAR_SAMPLES samples at $LIDAR_UPDATE_RATE Hz)."
