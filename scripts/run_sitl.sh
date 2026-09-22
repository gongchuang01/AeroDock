#!/usr/bin/env bash
set -euo pipefail
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
LOG_DIR="$AERODOCK_HOME/logs"
CMD_FILE="/tmp/aerodock-px4-commands"
mkdir -p "$LOG_DIR"
: > "$CMD_FILE"

if ! pgrep -f "MicroXRCEAgent udp4 -p 8888" >/dev/null; then
  nohup "$AERODOCK_HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" udp4 -p 8888 \
    > "$LOG_DIR/xrce-runtime.log" 2>&1 &
  echo $! > "$LOG_DIR/xrce.pid"
fi

nohup setsid sh -c "tail -n 0 -f $CMD_FILE | env SVGA_VGPU10=0 HEADLESS=1 make -C $AERODOCK_HOME/PX4-Autopilot px4_sitl gz_x500" \
  > "$LOG_DIR/px4-sitl.log" 2>&1 &
echo $! > "$LOG_DIR/px4-sitl.pid"

for _ in $(seq 1 30); do
  grep -q "Startup script returned successfully" "$LOG_DIR/px4-sitl.log" && break
  sleep 1
done
echo "param set NAV_DLL_ACT 0" >> "$CMD_FILE"
echo "PX4 SITL and DDS Agent are ready."
