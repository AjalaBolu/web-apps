"""Populate the database with demo stops, routes, shuttles and users.

!! Stop coordinates below are PLACEHOLDERS laid out in a small area. Replace
them with your real campus coordinates (in OpenStreetMap, right-click a spot ->
"Show address" gives lat/lng). Nothing else in the code needs to change.

Passwords come from SEED_*_PASSWORD env vars; if unset, random ones are
generated and printed ONCE here. No passwords are stored in the code.
"""
import os
import secrets

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

from db import get_conn, init_db  # noqa: E402

STOPS = [
    ("Main Gate",            7.4900, 5.2300),
    ("Administrative Block", 7.4915, 5.2312),
    ("Lecture Theatre",      7.4930, 5.2325),
    ("Library",              7.4940, 5.2340),
    ("Student Hostel",       7.4925, 5.2360),
    ("Cafeteria",            7.4910, 5.2345),
]

ROUTES = {
    "Main Loop": ["Main Gate", "Administrative Block", "Lecture Theatre", "Library", "Student Hostel"],
    "Hostel Express": ["Student Hostel", "Cafeteria", "Administrative Block", "Main Gate"],
}

# (shuttle number, driver email or None)
SHUTTLES = [
    ("Shuttle 01", "driver1@campus.test"),
    ("Shuttle 02", "driver2@campus.test"),
    ("Shuttle 03", None),
]

# (name, email, role, env var holding the password)
USERS = [
    ("Admin",     "admin@campus.test",   "admin",   "SEED_ADMIN_PASSWORD"),
    ("Driver 1",  "driver1@campus.test", "driver",  "SEED_DRIVER_PASSWORD"),
    ("Driver 2",  "driver2@campus.test", "driver",  "SEED_DRIVER_PASSWORD"),
    ("Student",   "student@campus.test", "student", "SEED_STUDENT_PASSWORD"),
]


def seed():
    init_db()
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM stops").fetchone()[0]:
        print("Database already seeded - delete shuttle.db to start over.")
        conn.close()
        return

    for name, lat, lng in STOPS:
        conn.execute("INSERT INTO stops (name, latitude, longitude) VALUES (?,?,?)", (name, lat, lng))
    for route_name, stop_names in ROUTES.items():
        rid = conn.execute("INSERT INTO routes (name) VALUES (?)", (route_name,)).lastrowid
        for seq, sname in enumerate(stop_names, start=1):
            sid = conn.execute("SELECT id FROM stops WHERE name=?", (sname,)).fetchone()[0]
            conn.execute("INSERT INTO route_stops (route_id, stop_id, sequence) VALUES (?,?,?)", (rid, sid, seq))

    generated = {}
    for name, email, role, env in USERS:
        pw = os.environ.get(env) or generated.setdefault(env, secrets.token_urlsafe(9))
        conn.execute("INSERT INTO users (name, email, password_hash, role) VALUES (?,?,?,?)",
                     (name, email, generate_password_hash(pw), role))

    for number, driver_email in SHUTTLES:
        driver_id = None
        if driver_email:
            driver_id = conn.execute("SELECT id FROM users WHERE email=?", (driver_email,)).fetchone()[0]
        conn.execute("INSERT INTO shuttles (shuttle_number, driver_id, status) VALUES (?,?, 'offline')",
                     (number, driver_id))
    conn.commit()
    conn.close()

    print("Seeded %d stops, %d routes, %d shuttles, %d users." % (len(STOPS), len(ROUTES), len(SHUTTLES), len(USERS)))
    print("\nDemo accounts:")
    for name, email, role, env in USERS:
        pw = os.environ.get(env) or generated[env]
        shown = pw if env in generated else "(from %s)" % env
        print("  %-8s %-22s password: %s" % (role, email, shown))
    if generated:
        print("\nSave these passwords now - random ones are shown only once.")


if __name__ == "__main__":
    seed()
