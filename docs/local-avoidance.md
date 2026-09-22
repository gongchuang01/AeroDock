# Local avoidance planner

The local planner consumes the 2D lidar scan and PX4 local position. It divides the scan into front, left, and right sectors.

When the front sector remains below the trigger distance for three scans, the planner compares median left and right clearance, selects the freer side, and converts a body-frame forward/lateral offset into a temporary PX4 NED waypoint.

Outputs:

- `/aerodock/avoidance/detour`  `geometry_msgs/PointStamped`, frame `px4_ned_altitude`
- `/aerodock/avoidance/decision`  human-readable decision and measurements

The planner requires an armed vehicle by default. The first sensor validation measured front=4.38 m, left=5.02 m, right=6.33 m and correctly selected a right detour.

Run after the obstacle simulator:

```bash
./scripts/run_local_avoidance.sh
```

This milestone generates and validates detour candidates. The next milestone connects those candidates to the Offboard mission state machine.
