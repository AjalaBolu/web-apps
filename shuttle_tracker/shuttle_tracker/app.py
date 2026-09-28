"""Campus Shuttle Tracking - Flask REST API with login and roles."""
import os
import sqlite3
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request, send_from_directory, session
from werkzeug.security import check_password_hash

load_dotenv()

import simulator  # noqa: E402  (after load_dotenv so env vars apply)
from db import get_conn, init_db  # noqa: E402
from eta import arrival_radius_m, eta_seconds, haversine_m  # noqa: E402

app = Flask(__name__, static_folder="static", static_url_path="/static")
_secret = os.environ.get("SECRET_KEY")
if not _secret or _secret.startswith("replace-with"):
    print("WARNING: SECRET_KEY not set - using a temporary key (logins reset on restart).")
    _secret = os.urandom(32).hex()
app.config.update(
    SECRET_KEY=_secret,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(os.environ.get("RENDER")),  # Render sets RENDER and serves HTTPS
)


# ---------- helpers ----------
def error(message, code):
    return jsonify({"error": message}), code


def valid_coords(lat, lng):
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    return lat, lng


def latest_location(conn, shuttle_id):
    row = conn.execute(
        "SELECT latitude, longitude, timestamp FROM locations WHERE shuttle_id=? ORDER BY id DESC LIMIT 1",
        (shuttle_id,),
    ).fetchone()
    return dict(row) if row else None


def shuttle_dict(conn, row):
    d = dict(row)
    d["location"] = latest_location(conn, row["id"])
    trip = conn.execute(
        "SELECT id, route_id FROM trips WHERE shuttle_id=? AND status='active'", (row["id"],)
    ).fetchone()
    d["active_trip"] = dict(trip) if trip else None
    return d


def route_stops(conn, route_id):
    rows = conn.execute(
        """SELECT s.id, s.name, s.latitude, s.longitude, rs.sequence
           FROM route_stops rs JOIN stops s ON s.id = rs.stop_id
           WHERE rs.route_id=? ORDER BY rs.sequence""",
        (route_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def user_payload(conn, user):
    shuttle = conn.execute("SELECT id FROM shuttles WHERE driver_id=?", (user["id"],)).fetchone()
    return {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"],
            "shuttle_id": shuttle["id"] if shuttle else None}


def require_role(*roles):
    """Require a logged-in user; if roles are given the user must have one of them."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            uid = session.get("uid")
            if not uid:
                return error("Please log in.", 401)
            conn = get_conn()
            try:
                user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
            finally:
                conn.close()
            if not user:
                session.clear()
                return error("Please log in.", 401)
            if roles and user["role"] not in roles:
                return error("You do not have permission to do that.", 403)
            g.user = dict(user)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def can_control(shuttle):
    return g.user["role"] == "admin" or shuttle["driver_id"] == g.user["id"]


@app.errorhandler(sqlite3.Error)
def handle_db_error(exc):
    app.logger.exception("Database error")
    return error("Database error. Please try again shortly.", 500)


@app.errorhandler(404)
def handle_404(exc):
    return error("Resource not found.", 404)


@app.errorhandler(405)
def handle_405(exc):
    return error("Method not allowed.", 405)


# ---------- pages ----------
@app.get("/")
def page_student():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/login")
def page_login():
    return send_from_directory(app.static_folder, "login.html")


@app.get("/driver")
def page_driver():
    return send_from_directory(app.static_folder, "driver.html")


@app.get("/admin")
def page_admin():
    return send_from_directory(app.static_folder, "admin.html")


# ---------- auth ----------
@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    if not email or not password:
        return error("Email and password are required.", 400)
    conn = get_conn()
    try:
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not check_password_hash(user["password_hash"], password):
            return error("Invalid email or password.", 401)
        session.clear()
        session["uid"] = user["id"]
        return jsonify(user_payload(conn, user))
    finally:
        conn.close()


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.get("/api/me")
@require_role()
def me():
    conn = get_conn()
    try:
        return jsonify(user_payload(conn, g.user))
    finally:
        conn.close()


# ---------- read endpoints (any logged-in user) ----------
@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/shuttles")
@require_role()
def list_shuttles():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM shuttles ORDER BY shuttle_number").fetchall()
        return jsonify([shuttle_dict(conn, r) for r in rows])  # empty list is valid
    finally:
        conn.close()


@app.get("/api/shuttles/<int:shuttle_id>")
@require_role()
def get_shuttle(shuttle_id):
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not row:
            return error("Shuttle not found.", 404)
        return jsonify(shuttle_dict(conn, row))
    finally:
        conn.close()


@app.get("/api/shuttles/<int:shuttle_id>/location")
@require_role()
def get_location(shuttle_id):
    conn = get_conn()
    try:
        if not conn.execute("SELECT 1 FROM shuttles WHERE id=?", (shuttle_id,)).fetchone():
            return error("Shuttle not found.", 404)
        loc = latest_location(conn, shuttle_id)
        if not loc:
            return error("No location available for this shuttle yet.", 404)
        return jsonify(loc)
    finally:
        conn.close()


@app.get("/api/stops")
@require_role()
def list_stops():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM stops ORDER BY id").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/api/routes")
@require_role()
def list_routes():
    conn = get_conn()
    try:
        out = [{"id": r["id"], "name": r["name"], "stops": route_stops(conn, r["id"])}
               for r in conn.execute("SELECT * FROM routes ORDER BY id").fetchall()]
        return jsonify(out)
    finally:
        conn.close()


@app.get("/api/eta/<int:shuttle_id>")
@require_role()
def get_eta(shuttle_id):
    stop_id = request.args.get("stop_id", type=int)
    if stop_id is None:
        return error("stop_id query parameter is required.", 400)
    conn = get_conn()
    try:
        shuttle = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not shuttle:
            return error("Shuttle not found.", 404)
        stop = conn.execute("SELECT * FROM stops WHERE id=?", (stop_id,)).fetchone()
        if not stop:
            return error("Destination stop not found.", 404)
        if shuttle["status"] != "active":
            return error("Shuttle is offline - no ETA available.", 409)
        loc = latest_location(conn, shuttle_id)
        if not loc:
            return error("Shuttle has no location yet.", 409)

        dist = haversine_m(loc["latitude"], loc["longitude"], stop["latitude"], stop["longitude"])
        arrived = dist <= arrival_radius_m()
        return jsonify({
            "shuttle_id": shuttle_id,
            "shuttle_number": shuttle["shuttle_number"],
            "destination": stop["name"],
            "distance_m": round(dist, 1),
            "eta_seconds": 0 if arrived else round(eta_seconds(dist)),
            "arrived": arrived,
            "current_location": loc,
        })
    finally:
        conn.close()


# ---------- trips (driver for own shuttle, or admin) ----------
@app.post("/api/trips/start")
@require_role("driver", "admin")
def start_trip():
    data = request.get_json(silent=True) or {}
    shuttle_id, route_id = data.get("shuttle_id"), data.get("route_id")
    if not isinstance(shuttle_id, int) or not isinstance(route_id, int):
        return error("shuttle_id and route_id (integers) are required.", 400)
    conn = get_conn()
    try:
        shuttle = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not shuttle:
            return error("Shuttle not found.", 404)
        if not can_control(shuttle):
            return error("You can only control your assigned shuttle.", 403)
        if not conn.execute("SELECT 1 FROM routes WHERE id=?", (route_id,)).fetchone():
            return error("Route not found.", 404)
        stops = route_stops(conn, route_id)
        if len(stops) < 2:
            return error("This route needs at least two stops.", 400)
        if conn.execute("SELECT 1 FROM trips WHERE shuttle_id=? AND status='active'", (shuttle_id,)).fetchone():
            return error("This shuttle already has an active trip.", 409)
        trip_id = conn.execute("INSERT INTO trips (shuttle_id, route_id) VALUES (?,?)",
                               (shuttle_id, route_id)).lastrowid
        conn.execute("UPDATE shuttles SET status='active' WHERE id=?", (shuttle_id,))
        conn.commit()
    finally:
        conn.close()
    simulator.start(shuttle_id, stops)  # simulated GPS begins sending locations
    return jsonify({"trip_id": trip_id, "shuttle_id": shuttle_id, "route_id": route_id, "status": "active"}), 201


@app.post("/api/trips/stop")
@require_role("driver", "admin")
def stop_trip():
    data = request.get_json(silent=True) or {}
    shuttle_id = data.get("shuttle_id")
    if not isinstance(shuttle_id, int):
        return error("shuttle_id (integer) is required.", 400)
    conn = get_conn()
    try:
        shuttle = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not shuttle:
            return error("Shuttle not found.", 404)
        if not can_control(shuttle):
            return error("You can only control your assigned shuttle.", 403)
        trip = conn.execute("SELECT id FROM trips WHERE shuttle_id=? AND status='active'", (shuttle_id,)).fetchone()
        if not trip:
            return error("No active trip for this shuttle.", 404)
        simulator.stop(shuttle_id)
        conn.execute("UPDATE trips SET status='completed', end_time=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?",
                     (trip["id"],))
        conn.execute("UPDATE shuttles SET status='offline' WHERE id=?", (shuttle_id,))
        conn.commit()
        return jsonify({"trip_id": trip["id"], "status": "completed"})
    finally:
        conn.close()


@app.post("/api/shuttles/<int:shuttle_id>/location")
@require_role("driver", "admin")
def post_location(shuttle_id):
    """Entry point a real GPS device would use. The simulator writes directly to the DB."""
    data = request.get_json(silent=True) or {}
    coords = valid_coords(data.get("lat"), data.get("lng"))
    if not coords:
        return error("Valid lat and lng are required.", 400)
    conn = get_conn()
    try:
        shuttle = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not shuttle:
            return error("Shuttle not found.", 404)
        if not can_control(shuttle):
            return error("You can only update your assigned shuttle.", 403)
        if shuttle["status"] != "active":
            return error("Shuttle is offline. Start a trip first.", 409)
        conn.execute("INSERT INTO locations (shuttle_id, latitude, longitude) VALUES (?,?,?)", (shuttle_id, *coords))
        conn.commit()
        return jsonify({"ok": True}), 201
    finally:
        conn.close()


# ---------- admin ----------
@app.get("/api/trips")
@require_role("admin")
def list_trips():
    status = request.args.get("status")
    query = """SELECT t.*, s.shuttle_number, r.name AS route_name
               FROM trips t JOIN shuttles s ON s.id = t.shuttle_id JOIN routes r ON r.id = t.route_id"""
    conn = get_conn()
    try:
        if status:
            rows = conn.execute(query + " WHERE t.status=? ORDER BY t.id DESC", (status,)).fetchall()
        else:
            rows = conn.execute(query + " ORDER BY t.id DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


@app.get("/api/drivers")
@require_role("admin")
def list_drivers():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id, name, email FROM users WHERE role='driver' ORDER BY name").fetchall()
        return jsonify([dict(r) for r in rows])
    finally:
        conn.close()


def check_driver(conn, driver_id):
    """None is fine (unassigned); otherwise it must be an existing driver user."""
    if driver_id is None:
        return True
    return isinstance(driver_id, int) and conn.execute(
        "SELECT 1 FROM users WHERE id=? AND role='driver'", (driver_id,)).fetchone() is not None


@app.post("/api/shuttles")
@require_role("admin")
def add_shuttle():
    data = request.get_json(silent=True) or {}
    number = str(data.get("shuttle_number", "")).strip()
    driver_id = data.get("driver_id")
    if not number or len(number) > 30:
        return error("Shuttle number is required (max 30 characters).", 400)
    conn = get_conn()
    try:
        if not check_driver(conn, driver_id):
            return error("Driver not found.", 400)
        try:
            new_id = conn.execute("INSERT INTO shuttles (shuttle_number, driver_id) VALUES (?,?)",
                                  (number, driver_id)).lastrowid
        except sqlite3.IntegrityError:
            return error("That shuttle number already exists.", 409)
        conn.commit()
        return jsonify({"id": new_id}), 201
    finally:
        conn.close()


@app.put("/api/shuttles/<int:shuttle_id>")
@require_role("admin")
def edit_shuttle(shuttle_id):
    data = request.get_json(silent=True) or {}
    conn = get_conn()
    try:
        shuttle = conn.execute("SELECT * FROM shuttles WHERE id=?", (shuttle_id,)).fetchone()
        if not shuttle:
            return error("Shuttle not found.", 404)
        number = str(data.get("shuttle_number", shuttle["shuttle_number"])).strip()
        driver_id = data.get("driver_id", shuttle["driver_id"])
        if not number or len(number) > 30:
            return error("Shuttle number is required (max 30 characters).", 400)
        if not check_driver(conn, driver_id):
            return error("Driver not found.", 400)
        try:
            conn.execute("UPDATE shuttles SET shuttle_number=?, driver_id=? WHERE id=?", (number, driver_id, shuttle_id))
        except sqlite3.IntegrityError:
            return error("That shuttle number already exists.", 409)
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


@app.delete("/api/shuttles/<int:shuttle_id>")
@require_role("admin")
def delete_shuttle(shuttle_id):
    conn = get_conn()
    try:
        if not conn.execute("SELECT 1 FROM shuttles WHERE id=?", (shuttle_id,)).fetchone():
            return error("Shuttle not found.", 404)
        simulator.stop(shuttle_id)
        conn.execute("DELETE FROM shuttles WHERE id=?", (shuttle_id,))
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


def parse_stop(data):
    name = str(data.get("name", "")).strip()
    coords = valid_coords(data.get("latitude"), data.get("longitude"))
    if not name or len(name) > 60 or not coords:
        return None
    return name, coords[0], coords[1]


@app.post("/api/stops")
@require_role("admin")
def add_stop():
    parsed = parse_stop(request.get_json(silent=True) or {})
    if not parsed:
        return error("A name and valid latitude/longitude are required.", 400)
    conn = get_conn()
    try:
        try:
            new_id = conn.execute("INSERT INTO stops (name, latitude, longitude) VALUES (?,?,?)", parsed).lastrowid
        except sqlite3.IntegrityError:
            return error("A stop with that name already exists.", 409)
        conn.commit()
        return jsonify({"id": new_id}), 201
    finally:
        conn.close()


@app.put("/api/stops/<int:stop_id>")
@require_role("admin")
def edit_stop(stop_id):
    parsed = parse_stop(request.get_json(silent=True) or {})
    if not parsed:
        return error("A name and valid latitude/longitude are required.", 400)
    conn = get_conn()
    try:
        if not conn.execute("SELECT 1 FROM stops WHERE id=?", (stop_id,)).fetchone():
            return error("Stop not found.", 404)
        try:
            conn.execute("UPDATE stops SET name=?, latitude=?, longitude=? WHERE id=?", (*parsed, stop_id))
        except sqlite3.IntegrityError:
            return error("A stop with that name already exists.", 409)
        conn.commit()
        return jsonify({"ok": True})
    finally:
        conn.close()


init_db()
simulator.reset_stale()

if __name__ == "__main__":
    # use_reloader=False so simulation threads are not duplicated/killed by the reloader
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", use_reloader=False, port=5000)
