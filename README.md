# AeroDock

A ROS 2 Humble and PX4 project for autonomous UAV mission execution in Gazebo Harmonic.

## Current milestone

The C++ Offboard controller runs a safety-aware state machine:

1. stream position setpoints before mode switching;
2. request Offboard mode and arm;
3. climb to a configurable NED position;
4. hover while reporting measured altitude;
5. command landing and wait for automatic disarm;
6. fall back to landing on arming or mission timeout.

The first verified simulation reached 2.93 m for a 3.0 m target, landed, disarmed, and exited normally.

## Stack

- Ubuntu 22.04
- ROS 2 Humble
- PX4 v1.16
- Gazebo Harmonic
- Micro XRCE-DDS Agent
- C++17 / rclcpp

## Repository layout

- `src/aerodock_offboard`: ROS 2 mission controller
- `scripts/run_sitl.sh`: start PX4, Gazebo, and DDS bridge
- `scripts/run_mission.sh`: launch the mission
- `scripts/stop.sh`: stop the simulation
- `docs`: architecture and validation notes

## Run

```bash
./scripts/run_sitl.sh
./scripts/run_mission.sh
```

Change target height and hover time in `src/aerodock_offboard/config/mission.yaml`.

> `NAV_DLL_ACT=0` is applied only by the SITL helper because this headless VM has no ground-control station. Do not copy that setting to a real aircraft.
