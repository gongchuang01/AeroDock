# Project status

## Implemented

- PX4 SITL, Gazebo Harmonic, ROS 2 Humble, and uXRCE-DDS integration
- C++ Offboard takeoff, hover, landing, and five-waypoint state machines
- CSV telemetry and quantitative flight analysis
- Gazebo and RViz route/trajectory visualization
- 2D lidar bridge, persistence filtering, and emergency landing supervisor
- reactive left/right local avoidance with configurable sensor mounting yaw
- temporary detour execution followed by original-route resumption
- automatic launch shutdown and pass/fail telemetry validation

## Verified benchmark

A recorded integrated run climbed to 3 m, detected an obstacle at 1.91 m, selected the clearer side, reached the detour at 2.85 m altitude, resumed the five-waypoint route, landed, and disarmed. The acceptance tool checks waypoint accuracy, detour accuracy, climb height, landing state, and final altitude.

## Known limitations

- The planner is reactive and does not build an occupancy map or optimize a full trajectory.
- The simulated `gpu_lidar` requires OpenGL 3.3. VMware rendering and PX4 lockstep timing can make repeated runs non-deterministic on a 4-core VM.
- The current controller uses position setpoints with fixed yaw; it does not yet generate velocity-limited, dynamically feasible trajectories.
- Dynamic obstacle tracking, replanning, and hardware-in-the-loop validation remain future work.
