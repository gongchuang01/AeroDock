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


## Waypoint mission

Run a 3 m altitude square route and return to the launch point:

```bash
./scripts/run_sitl.sh
./scripts/run_waypoints.sh
python3 tools/analyze_flight.py ~/aerodock/logs/waypoint-flight.csv
./scripts/stop.sh
```

The waypoint controller requires both spatial tolerance and a stability hold time before advancing. Every flight produces CSV telemetry for reproducible evaluation. See `docs/flight-validation.md`.


## Visual simulation

To watch the aircraft and its route on the Ubuntu desktop, run these in separate terminals:

```bash
./scripts/run_visual_sim.sh
./scripts/run_visualization.sh
./scripts/run_waypoints.sh
```

Gazebo shows the physical X500 flight. RViz2 shows numbered waypoints, the planned route, and the measured trajectory. See `docs/visual-simulation.md`.
