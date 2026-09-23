# Verified flight artifact

`verified-avoidance.csv` is the raw telemetry from the final accepted PX4 SITL and Gazebo obstacle-avoidance run on Ubuntu 22.04 with ROS 2 Humble and PX4 v1.16.

Re-run the acceptance checks:

```bash
python3 tools/validate_avoidance.py artifacts/flight/verified-avoidance.csv
python3 tools/analyze_flight.py artifacts/flight/verified-avoidance.csv
```

The recording contains 98 samples over 50.4 seconds. It is committed as a regression fixture so changes to analysis or validation logic are checked against a real successful mission.
