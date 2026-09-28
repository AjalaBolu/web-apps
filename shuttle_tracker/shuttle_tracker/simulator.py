"""Simulated GPS service.

Behaves like a tracker fitted to the shuttle: when a trip starts, a background
thread writes a new lat/lng to the database every few seconds along the
route's stops. At the last stop it dwells briefly (so "Arrived" is visible),
then completes the trip. No GPS hardware involved.

In production this module would be replaced by a real GPS device posting to
POST /api/shuttles/<id>/location.
"""
import os
import threading

from db import get_conn
from eta import avg_speed_kmh, haversine_m

_running = {}  # shuttle_id -> threading.Event used to stop that simulation
_lock = threading.Lock()


def interval_sec():
    return float(os.environ.get("SIM_INTERVAL_SEC", "2"))


def path_points(stops, step_m):
    """Turn stop-to-stop legs into evenly spaced points (~step_m apart)."""
    points = [(stops[0]["latitude"], stops[0]["longitude"])]
    for a, b in zip(stops, stops[1:]):
        dist = haversine_m(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
        n = max(1, round(dist / step_m))
        for i in range(1, n + 1):
            f = i / n
            points.append((
                a["latitude"] + (b["latitude"] - a["latitude"]) * f,
                a["longitude"] + (b["longitude"] - a["longitude"]) * f,
            ))
    return points


def _finish_trip(shuttle_id):
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE trips SET status='completed', end_time=strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE shuttle_id=? AND status='active'", (shuttle_id,))
        conn.execute("UPDATE shuttles SET status='offline' WHERE id=?", (shuttle_id,))
        conn.commit()
    finally:
        conn.close()


def _run(shuttle_id, points, stop_event):
    try:
        for lat, lng in points:
            if stop_event.is_set():
                return
            conn = get_conn()
            try:
                conn.execute("INSERT INTO locations (shuttle_id, latitude, longitude) VALUES (?,?,?)",
                             (shuttle_id, lat, lng))
                conn.commit()
            finally:
                conn.close()
            if stop_event.wait(interval_sec()):
                return
        if stop_event.wait(interval_sec() * 3):  # dwell at the final stop
            return
        _finish_trip(shuttle_id)
    except Exception as exc:  # keep the app alive if a simulation thread fails
        print("Simulator error for shuttle %s: %s" % (shuttle_id, exc))
        try:
            _finish_trip(shuttle_id)
        except Exception:
            pass
    finally:
        with _lock:
            if _running.get(shuttle_id) is stop_event:
                del _running[shuttle_id]


def start(shuttle_id, route_stops):
    """route_stops: list of dicts with latitude/longitude, in travel order."""
    step_m = avg_speed_kmh() * 1000 / 3600 * interval_sec()
    points = path_points(route_stops, step_m)
    event = threading.Event()
    with _lock:
        old = _running.get(shuttle_id)
        if old:
            old.set()
        _running[shuttle_id] = event
    threading.Thread(target=_run, args=(shuttle_id, points, event), daemon=True).start()


def stop(shuttle_id):
    with _lock:
        event = _running.get(shuttle_id)
    if event:
        event.set()


def reset_stale():
    """After a restart no simulation threads exist, so close any 'active' trips."""
    conn = get_conn()
    try:
        conn.execute("UPDATE trips SET status='completed', end_time=strftime('%Y-%m-%dT%H:%M:%fZ','now') "
                     "WHERE status='active'")
        conn.execute("UPDATE shuttles SET status='offline'")
        conn.commit()
    finally:
        conn.close()
