# Docker development environment

The container provides a reproducible Ubuntu 22.04 environment with ROS 2 Humble, PX4 v1.16 message definitions, AeroDock executables, and the planner unit tests. It supports Linux hosts and Docker Desktop on Windows or macOS.

## Build and open a shell

```bash
docker compose build
docker compose run --rm aerodock
```

Inside the container, verify the installed ROS 2 executables:

```bash
ros2 pkg executables aerodock_offboard
```

Run a specific node with `docker compose run`, for example:

```bash
docker compose run --rm aerodock ros2 run aerodock_offboard waypoint_mission
```

The image is intended for clean builds, unit tests, and ROS node development. PX4 SITL, Gazebo rendering, DDS networking, and hardware access require additional host integration. Use the documented Ubuntu 22.04 setup for the complete graphical simulation.

The PX4 message branch can be overridden when building directly:

```bash
docker build --build-arg PX4_MSGS_REF=release/1.16 -t aerodock:humble .
```
