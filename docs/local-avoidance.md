# Local avoidance planner

The planner consumes the Gazebo 2D lidar scan together with PX4 local position and vehicle status. It divides the scan into front, left, and right sectors.

After the front sector remains below the trigger distance for three scans, it compares median clearance on both sides, chooses the freer side, and converts a sensor-frame forward/lateral offset into a temporary PX4 NED waypoint.

The configurable `sensor_yaw_offset_deg` accounts for the lidar mounting orientation before converting targets into NED coordinates. Safety gates prevent detours while the vehicle is disarmed, while local position is invalid, or below the configured 2 m flight altitude. The waypoint mission accepts valid detours only while armed and navigating. It flies to the temporary target, holds position, then resumes the interrupted route. A 20 second detour timeout commands landing.

Outputs:

- `/aerodock/avoidance/detour`: `geometry_msgs/PointStamped`, frame `px4_ned_altitude`
- `/aerodock/avoidance/decision`: human-readable decision and lidar measurements

Run the integrated mission:

```bash
./scripts/run_obstacle_sim.sh
./scripts/run_avoidance_mission.sh
./scripts/stop.sh
```

The repository stores a compact single-obstacle acceptance world and a dedicated square avoidance route. The ground collision plane is 100 x 100 m.

The verified run climbed to 3 m, completed five route waypoints, detected an obstacle at 1.91 m, selected the right side from measured clearances, reached a detour at 2.85 m altitude, resumed the route, landed, and disarmed automatically.
