#!/usr/bin/env python3
"""Render a dependency-free SVG summary from AeroDock CSV telemetry."""
import csv
import sys
from pathlib import Path

source = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/flight/verified-avoidance.csv")
destination = Path(sys.argv[2] if len(sys.argv) > 2 else "artifacts/flight/verified-avoidance.svg")
with source.open(newline="") as stream:
    rows = list(csv.DictReader(stream))
if not rows:
    raise SystemExit("No telemetry samples found")

values = lambda key: [float(row[key]) for row in rows]
xs, ys, ts, zs = values("x_m"), values("y_m"), values("time_s"), values("altitude_m")
targets = []
for row in rows:
    point = (float(row["target_x_m"]), float(row["target_y_m"]), row["state"])
    if not targets or point[:2] != targets[-1][:2]:
        targets.append(point)

width, height = 1200, 620
plot_x, plot_y, plot_w, plot_h = 70, 100, 510, 430
alt_x, alt_y, alt_w, alt_h = 650, 100, 500, 430
pad = 0.35
xmin, xmax = min(xs + [p[0] for p in targets]) - pad, max(xs + [p[0] for p in targets]) + pad
ymin, ymax = min(ys + [p[1] for p in targets]) - pad, max(ys + [p[1] for p in targets]) + pad
tmin, tmax = min(ts), max(ts)
zmin, zmax = 0.0, max(zs) + 0.35

def scale(v, lo, hi, a, b):
    return a + (v - lo) * (b - a) / (hi - lo or 1)

def path(points):
    return " ".join(("M" if i == 0 else "L") + f" {x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))

flight = [(scale(x, xmin, xmax, plot_x, plot_x + plot_w), scale(y, ymin, ymax, plot_y + plot_h, plot_y)) for x, y in zip(xs, ys)]
route = [(scale(x, xmin, xmax, plot_x, plot_x + plot_w), scale(y, ymin, ymax, plot_y + plot_h, plot_y)) for x, y, _ in targets]
altitude = [(scale(t, tmin, tmax, alt_x, alt_x + alt_w), scale(z, zmin, zmax, alt_y + alt_h, alt_y)) for t, z in zip(ts, zs)]
parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">AeroDock verified autonomous flight</title>
<desc id="desc">Top-down flight path with lidar detour and altitude over time.</desc>
<rect width="100%" height="100%" rx="22" fill="#0b1220"/>
<style>text{{font-family:Inter,Segoe UI,sans-serif;fill:#dbeafe}}.muted{{fill:#94a3b8}}.grid{{stroke:#233047;stroke-width:1}}.axis{{stroke:#64748b;stroke-width:1.5}}</style>
<text x="60" y="48" font-size="26" font-weight="700">Verified autonomous flight</text>
<text x="60" y="75" font-size="14" class="muted">PX4 SITL · ROS 2 Humble · Gazebo Harmonic · 98 telemetry samples</text>
<text x="{plot_x}" y="{plot_y-20}" font-size="18" font-weight="600">Top-down route (m)</text>
<text x="{alt_x}" y="{alt_y-20}" font-size="18" font-weight="600">Altitude profile</text>''']
for i in range(6):
    gx = plot_x + i * plot_w / 5
    gy = plot_y + i * plot_h / 5
    ax = alt_x + i * alt_w / 5
    ay = alt_y + i * alt_h / 5
    parts += [f'<line class="grid" x1="{gx:.1f}" y1="{plot_y}" x2="{gx:.1f}" y2="{plot_y+plot_h}"/>', f'<line class="grid" x1="{plot_x}" y1="{gy:.1f}" x2="{plot_x+plot_w}" y2="{gy:.1f}"/>', f'<line class="grid" x1="{ax:.1f}" y1="{alt_y}" x2="{ax:.1f}" y2="{alt_y+alt_h}"/>', f'<line class="grid" x1="{alt_x}" y1="{ay:.1f}" x2="{alt_x+alt_w}" y2="{ay:.1f}"/>']
parts += [f'<path d="{path(route)}" fill="none" stroke="#64748b" stroke-width="2" stroke-dasharray="7 7"/>', f'<path d="{path(flight)}" fill="none" stroke="#22d3ee" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>']
for index, ((px, py), (_, _, state)) in enumerate(zip(route, targets)):
    color = "#f59e0b" if state == "DETOUR" else "#a78bfa"
    label = "D" if state == "DETOUR" else str(index + 1)
    parts += [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="{color}" stroke="#0b1220" stroke-width="3"/>', f'<text x="{px+12:.1f}" y="{py-10:.1f}" font-size="13" font-weight="700">{label}</text>']
parts += [f'<path d="{path(altitude)}" fill="none" stroke="#34d399" stroke-width="4" stroke-linecap="round"/>', f'<line x1="{alt_x}" y1="{scale(3,zmin,zmax,alt_y+alt_h,alt_y):.1f}" x2="{alt_x+alt_w}" y2="{scale(3,zmin,zmax,alt_y+alt_h,alt_y):.1f}" stroke="#f59e0b" stroke-width="2" stroke-dasharray="7 7"/>', f'<text x="{alt_x+alt_w-92}" y="{scale(3,zmin,zmax,alt_y+alt_h,alt_y)-9:.1f}" font-size="13" fill="#f59e0b">3 m target</text>', f'<text x="{plot_x}" y="570" font-size="14" class="muted">Cyan: measured path  ·  Purple: mission waypoint  ·  Orange D: lidar detour</text>', f'<text x="{alt_x}" y="570" font-size="14" class="muted">Max {max(zs):.2f} m  ·  Final {zs[-1]:.2f} m  ·  Duration {ts[-1]:.1f} s</text>', '</svg>']
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text("\n".join(parts) + "\n", encoding="utf-8")
print(f"Rendered {destination} from {source}")
