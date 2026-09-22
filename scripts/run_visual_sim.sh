#!/usr/bin/env bash
set -euo pipefail
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
LOG_DIR="$AERODOCK_HOME/logs"
CMD_FILE="/tmp/aerodock-px4-commands"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/run/user/$(id -u)/gdm/Xauthority}"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
export QT_X11_NO_MITSHM=1
export LIBGL_ALWAYS_SOFTWARE=1
export SVGA_VGPU10=0
mkdir -p "$LOG_DIR"
: > "$CMD_FILE"
: > "$LOG_DIR/px4-visual.log"

if ! pgrep -f "MicroXRCEAgent udp4 -p 8888" >/dev/null; then
  nohup "$AERODOCK_HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" udp4 -p 8888 > "$LOG_DIR/xrce-runtime.log" 2>&1 &
fi
nohup setsid sh -c "tail -n 0 -f $CMD_FILE | env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS QT_X11_NO_MITSHM=1 LIBGL_ALWAYS_SOFTWARE=1 SVGA_VGPU10=0 make -C $AERODOCK_HOME/PX4-Autopilot px4_sitl gz_x500" > "$LOG_DIR/px4-visual.log" 2>&1 &

for _ in $(seq 1 45); do
  grep -q "Startup script returned successfully" "$LOG_DIR/px4-visual.log" && break
  sleep 1
done
if ! grep -q "Startup script returned successfully" "$LOG_DIR/px4-visual.log"; then
  echo "PX4 visual simulation failed to start. See $LOG_DIR/px4-visual.log" >&2
  exit 1
fi
echo "param set NAV_DLL_ACT 0" >> "$CMD_FILE"
echo "Gazebo visual simulation is ready on the Ubuntu desktop."
