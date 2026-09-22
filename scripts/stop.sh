#!/usr/bin/env bash
set -euo pipefail
pkill -f "build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -f "gz sim" 2>/dev/null || true
pkill -f "MicroXRCEAgent udp4 -p 8888" 2>/dev/null || true
pkill -f "tail -n 0 -f /tmp/aerodock-px4-commands" 2>/dev/null || true
pkill -f "rviz2.*aerodock.rviz" 2>/dev/null || true
pkill -f "trajectory_visualizer.py" 2>/dev/null || true
pkill -f "parameter_bridge" 2>/dev/null || true
pkill -f "tail -n 0 -f /tmp/aerodock-px4-obstacle-commands" 2>/dev/null || true
pkill -f "obstacle_safety.py" 2>/dev/null || true
pkill -f "local_avoidance.py" 2>/dev/null || true
echo "AeroDock simulation and visualization stopped."
