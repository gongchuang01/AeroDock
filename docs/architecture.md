# Architecture

```text
Gazebo obstacle world
  └─ X500 + 2D lidar
       ├─ PX4 SITL ── uXRCE-DDS/UDP 8888 ── Micro XRCE-DDS Agent
       │                                      │
       │                                      └─ ROS 2 PX4 topics
       └─ Gazebo LaserScan ── ros_gz_bridge ── /world/.../scan
                                                │
                                                v
                                     local_avoidance_planner
                                     - front/left/right sectors
                                     - persistence and hysteresis
                                     - sensor-to-NED transform
                                                │ PointStamped detour
                                                v
                                         waypoint_mission
                                     - Offboard/arming state machine
                                     - original waypoint or detour
                                     - hold, resume, timeout, land
                                                │
                                                v
                                      CSV telemetry + validator
```

The C++ mission controller runs at 10 Hz. It streams setpoints for two seconds before requesting Offboard mode, then confirms arming and mode changes from PX4 status messages. A five-waypoint route is advanced only after the vehicle remains within the configured 3D tolerance for the hold period.

The Python local planner consumes the 2D scan, local position, and vehicle status. Three consecutive blocked scans activate avoidance. Median left/right clearance selects a side, and the configured sensor mounting yaw converts the sensor-frame offset into a PX4 NED waypoint. The planner does not command the aircraft directly.

The mission controller owns flight authority. It ignores detours during takeoff, while disarmed, outside navigation, or while another detour is active. After reaching and holding a detour it resumes the interrupted waypoint. Mission, detour, arming, and flight-state timeouts all lead to landing.

The emergency obstacle supervisor is an independent safety path. It can command landing when an armed vehicle crosses the critical distance even if the local planner or mission route fails.
