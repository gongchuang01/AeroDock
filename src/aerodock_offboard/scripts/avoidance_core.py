#!/usr/bin/env python3
"""ROS-independent geometry and scan helpers for AeroDock local avoidance."""
import math
import statistics


def sector_values(ranges, angle_min, angle_increment, range_min, range_max,
                  low_deg, high_deg):
    """Return finite, in-range lidar samples inside an inclusive angle sector."""
    low = math.radians(low_deg)
    high = math.radians(high_deg)
    values = []
    angle = angle_min
    for distance in ranges:
        if low <= angle <= high and math.isfinite(distance):
            if range_min <= distance <= range_max:
                values.append(float(distance))
        angle += angle_increment
    return values


def clearance(values, range_max):
    """Use a robust median clearance, or sensor maximum for an empty sector."""
    return statistics.median(values) if values else float(range_max)


def detour_target(north, east, heading, sensor_yaw_offset,
                  forward_offset, lateral_offset, choose_left):
    """Convert a sensor-frame detour into PX4 local NED north/east coordinates."""
    lateral_right = -lateral_offset if choose_left else lateral_offset
    sensor_heading = heading + sensor_yaw_offset
    target_north = (north + forward_offset * math.cos(sensor_heading)
                    - lateral_right * math.sin(sensor_heading))
    target_east = (east + forward_offset * math.sin(sensor_heading)
                   + lateral_right * math.cos(sensor_heading))
    return target_north, target_east
