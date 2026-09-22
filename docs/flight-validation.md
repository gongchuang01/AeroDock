# Flight validation

## Square waypoint mission

The SITL mission used five NED waypoints:

| Waypoint | North (m) | East (m) | Altitude (m) |
|---:|---:|---:|---:|
| 1 | 0 | 0 | 3 |
| 2 | 3 | 0 | 3 |
| 3 | 3 | 3 | 3 |
| 4 | 0 | 3 | 3 |
| 5 | 0 | 0 | 3 |

Acceptance radius was 0.45 m, with a 1.5 s stability requirement. Observed arrival errors were 0.43, 0.42, 0.39, 0.34, and 0.39 m. PX4 completed landing and automatic disarm. The launch process exited with code 0.

Telemetry is written to `~/aerodock/logs/waypoint-flight.csv`. Run:

```bash
python3 tools/analyze_flight.py ~/aerodock/logs/waypoint-flight.csv
```
