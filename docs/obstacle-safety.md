# Obstacle safety

The obstacle simulation uses the PX4 `x500_lidar_2d` model in Gazebo Harmonic's `walls` world. A Harmonic-compatible ROS-Gazebo bridge converts the scan to `sensor_msgs/msg/LaserScan` at about 7.2 Hz.

`obstacle_safety.py` evaluates a configurable forward sector. It publishes:

- `/aerodock/obstacle/min_distance` as `std_msgs/Float32`
- `/aerodock/obstacle/blocked` as `std_msgs/Bool`

A hazard must be present for three consecutive scans before it is accepted. When the aircraft is armed and `action=land`, the supervisor sends a PX4 `VEHICLE_CMD_NAV_LAND` command once.

Run in separate terminals:

```bash
./scripts/run_obstacle_sim.sh
./scripts/run_obstacle_safety.sh
```

The initial validation measured a stable forward distance of 4.38 m. A test threshold of 5.0 m correctly changed the supervisor to the blocked state.
