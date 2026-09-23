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

The final integrated acceptance run completed in 50.4 s with 98 telemetry samples. It reached all five route waypoints within the 0.50 m threshold, executed the lidar-planned detour with 0.20 m minimum error, reached 3.09 m maximum altitude, entered the landing state, and finished at 0.07 m altitude. All seven validation checks passed.

The controller ignores new detour requests while holding inside a waypoint acceptance region. This prevents a persistent lidar return from replacing the final return-to-home hold and blocking the landing transition.

## Known limitations

- The planner is reactive and does not build an occupancy map or optimize a full trajectory.
- The simulated `gpu_lidar` requires OpenGL 3.3. VMware rendering and PX4 lockstep timing can make repeated runs non-deterministic on a 4-core VM.
- The current controller uses position setpoints with fixed yaw; it does not yet generate velocity-limited, dynamically feasible trajectories.
- Dynamic obstacle tracking, replanning, and hardware-in-the-loop validation remain future work.
