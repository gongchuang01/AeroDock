#!/usr/bin/env bash

# Non-interactive shells (for example SSH and CI) do not source the user's
# ROS environment automatically. Load the system installation when present so
# the command checks below report the installed environment accurately.
if [ -f /opt/ros/humble/setup.bash ]; then
  set +u
  source /opt/ros/humble/setup.bash
fi

set -u
AERODOCK_HOME="${AERODOCK_HOME:-$HOME/aerodock}"
failures=0
warnings=0

pass() { printf '[PASS] %s\n' "$1"; }
warn() { printf '[WARN] %s\n' "$1"; warnings=$((warnings + 1)); }
fail() { printf '[FAIL] %s\n' "$1"; failures=$((failures + 1)); }

printf 'AeroDock environment check\n'
printf 'OS: '; . /etc/os-release && printf '%s\n' "$PRETTY_NAME"
printf 'Architecture: %s, CPU cores: %s\n' "$(uname -m)" "$(nproc)"
LC_ALL=C free -h | awk '/Mem:/ {printf "Memory: %s total, %s available\n", $2, $7}'
LC_ALL=C df -h / | awk 'NR==2 {printf "Root disk: %s total, %s available (%s used)\n", $2, $4, $5}'

for command_name in ros2 colcon gz cmake git python3; do
  if command -v "$command_name" >/dev/null 2>&1; then
    pass "$command_name is available"
  else
    fail "$command_name is missing"
  fi
done

if [ "${ROS_DISTRO:-}" = "humble" ] || [ -f /opt/ros/humble/setup.bash ]; then
  pass 'ROS 2 Humble is installed'
else
  fail 'ROS 2 Humble is not installed'
fi

[ -d "$AERODOCK_HOME/PX4-Autopilot" ] && pass 'PX4 source tree found' || fail 'PX4 source tree missing'
[ -x "$AERODOCK_HOME/Micro-XRCE-DDS-Agent/build/MicroXRCEAgent" ] && pass 'Micro XRCE-DDS Agent found' || fail 'Micro XRCE-DDS Agent missing'
[ -f "$AERODOCK_HOME/ros2_ws/install/aerodock_offboard/share/aerodock_offboard/package.xml" ] && pass 'AeroDock ROS package is built' || warn 'AeroDock ROS package has not been built'

user_groups=" $(id -nG) "
[[ "$user_groups" == *' video '* ]] && pass 'user belongs to video group' || warn 'user is not in video group'
[[ "$user_groups" == *' render '* ]] && pass 'user belongs to render group' || warn 'user is not in render group'

if command -v glxinfo >/dev/null 2>&1 && [ -n "${DISPLAY:-}" ]; then
  if glxinfo -B >/tmp/aerodock-glxinfo.txt 2>&1; then
    gl_version=$(awk -F': ' '/OpenGL core profile version string/ {print $2; exit}' /tmp/aerodock-glxinfo.txt)
    pass "OpenGL context available${gl_version:+: $gl_version}"
  else
    warn "DISPLAY=$DISPLAY exists but OpenGL context creation failed"
  fi
else
  warn 'OpenGL was not checked; GPU lidar requires a working OpenGL 3.3 context'
fi

printf 'Result: %s failure(s), %s warning(s)\n' "$failures" "$warnings"
[ "$failures" -eq 0 ]
