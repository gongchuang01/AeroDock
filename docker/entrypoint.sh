#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /opt/aerodock_ws/install/setup.bash
exec "$@"
