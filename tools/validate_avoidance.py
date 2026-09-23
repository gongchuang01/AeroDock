#!/usr/bin/env python3
"""Validate an AeroDock integrated lidar-avoidance telemetry log."""
import csv
import sys
from collections import defaultdict
from pathlib import Path

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "aerodock/logs/waypoint-flight.csv"
with path.open(newline="") as stream:
    rows = list(csv.DictReader(stream))
if not rows:
    raise SystemExit("FAIL: no telemetry samples found")

states = {row["state"] for row in rows}
nav_errors = defaultdict(list)
for row in rows:
    if row["state"] == "NAVIGATING":
        nav_errors[int(row["waypoint"])].append(float(row["error_m"]))

detour_errors = [float(row["error_m"]) for row in rows if row["state"] == "DETOUR"]
max_altitude = max(float(row["altitude_m"]) for row in rows)
final_altitude = abs(float(rows[-1]["altitude_m"]))
checks = {
    "five waypoints approached": len(nav_errors) >= 5,
    "every waypoint reached 0.50 m tolerance": all(min(errors) <= 0.50 for errors in nav_errors.values()),
    "detour was executed": bool(detour_errors),
    "detour reached 0.50 m tolerance": bool(detour_errors) and min(detour_errors) <= 0.50,
    "nominal 3 m climb": 2.7 <= max_altitude <= 3.4,
    "landing state recorded": "LANDING" in states,
    "final altitude near ground": final_altitude <= 0.20,
}

print(f"AeroDock acceptance report: {path}")
for label, passed in checks.items():
    print(f"[{'PASS' if passed else 'FAIL'}] {label}")
print(f"samples={len(rows)}, max_altitude={max_altitude:.2f} m, final_altitude={final_altitude:.2f} m")
if detour_errors:
    print(f"detour_min_error={min(detour_errors):.2f} m")

if not all(checks.values()):
    raise SystemExit(1)
