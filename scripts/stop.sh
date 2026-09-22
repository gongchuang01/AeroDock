#!/usr/bin/env bash
set -euo pipefail
pkill -f "build/px4_sitl_default/bin/px4" 2>/dev/null || true
pkill -f "gz sim" 2>/dev/null || true
pkill -f "MicroXRCEAgent udp4 -p 8888" 2>/dev/null || true
pkill -f "tail -n 0 -f /tmp/aerodock-px4-commands" 2>/dev/null || true
echo "AeroDock simulation stopped."
