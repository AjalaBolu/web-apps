"""Distance and ETA helpers.

The prototype estimates ETA as: remaining straight-line distance / assumed
average shuttle speed. Real traffic and live road conditions are out of scope.
"""
import math
import os

EARTH_RADIUS_M = 6371000.0


def haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in metres between two lat/lng points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def avg_speed_kmh():
    return float(os.environ.get("AVG_SPEED_KMH", "20"))


def arrival_radius_m():
    return float(os.environ.get("ARRIVAL_RADIUS_M", "30"))


def eta_seconds(distance_m, speed_kmh=None):
    speed_ms = (speed_kmh or avg_speed_kmh()) * 1000 / 3600
    return distance_m / speed_ms
