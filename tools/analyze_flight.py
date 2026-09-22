#!/usr/bin/env python3
import csv
import math
import sys
from collections import defaultdict

path = sys.argv[1] if len(sys.argv) > 1 else "/home/gc/aerodock/logs/waypoint-flight.csv"
with open(path, newline="") as stream:
    rows = list(csv.DictReader(stream))
if not rows:
    raise SystemExit("No telemetry samples found")

nav = [r for r in rows if r["state"] == "NAVIGATING"]
by_waypoint = defaultdict(list)
for row in nav:
    by_waypoint[int(row["waypoint"]) + 1].append(float(row["error_m"]))

print(f"Telemetry: {path}")
print(f"Duration: {float(rows[-1]['time_s']):.1f} s")
print(f"Samples: {len(rows)}")
print(f"Maximum altitude: {max(float(r['altitude_m']) for r in rows):.2f} m")
for index in sorted(by_waypoint):
    errors = by_waypoint[index]
    rms = math.sqrt(sum(e * e for e in errors) / len(errors))
    print(f"Waypoint {index}: min error {min(errors):.2f} m, approach RMS {rms:.2f} m")
