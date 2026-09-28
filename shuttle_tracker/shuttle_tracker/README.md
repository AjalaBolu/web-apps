# Campus Shuttle Tracking - Prototype (all build phases + Render deployment files)

Simulated GPS -> Flask API -> SQLite -> student map, driver console, admin dashboard.
The prototype simulates GPS data using predefined geographical coordinates to
demonstrate the intended real-time tracking functionality. In a production
deployment, the simulated GPS source can be replaced with a physical
GPS-enabled tracking device installed on the shuttle.

## Run
    pip install -r requirements.txt
    cp .env.example .env           # set SECRET_KEY to a long random string
    python seed.py                 # creates shuttle.db + demo accounts (passwords printed ONCE)
    python app.py                  # http://127.0.0.1:5000

If you already have a shuttle.db from the earlier version, delete it before
running `python seed.py` (the schema is unchanged, but users are new).

## Pages
- `/login`  - everyone signs in here; you are sent to your role's page
- `/`       - student map: shuttles, stops, routes, destination + ETA
- `/driver` - driver console: choose route, Start Trip / Stop Trip, live location
- `/admin`  - admin: add/remove shuttles, assign drivers, edit/add stops, view active trips

## Demo accounts (created by seed.py)
admin@campus.test, driver1@campus.test (Shuttle 01), driver2@campus.test (Shuttle 02),
student@campus.test. Set SEED_*_PASSWORD in .env for fixed passwords, or use the
random ones printed by seed.py.

## Demo flow
1. Driver 1 logs in -> Start Trip (simulator begins sending positions).
2. Student logs in (another browser/incognito window) -> sees Shuttle 01 moving.
3. Student picks "Student Hostel" -> ETA counts down -> "Arrived" at the stop.
4. The trip completes automatically shortly after the last stop (or driver presses Stop Trip).

## Simulator
Runs inside the server while a trip is active. Settings in .env:
SIM_INTERVAL_SEC (seconds between updates) and AVG_SPEED_KMH (used for both
simulated movement and the ETA, so they stay consistent). For a quicker demo
raise AVG_SPEED_KMH; ETA stays accurate because it uses the same speed.

## Before your real demo
Replace the PLACEHOLDER stop coordinates in `seed.py` (or edit them in the
admin page after seeding).

## Endpoints (login required; role in brackets)
POST /api/login | /api/logout ; GET /api/me
GET  /api/shuttles | /api/shuttles/<id> | /api/shuttles/<id>/location | /api/stops | /api/routes | /api/eta/<id>?stop_id=
POST /api/trips/start {shuttle_id, route_id} | /api/trips/stop {shuttle_id}   [driver: own shuttle, admin]
POST /api/shuttles/<id>/location {lat, lng}   [driver/admin - the route a real GPS device would use]
GET  /api/trips[?status=active] | /api/drivers   [admin]
POST /api/shuttles, PUT/DELETE /api/shuttles/<id>, POST /api/stops, PUT /api/stops/<id>   [admin]

## ETA (for your documentation)
ETA = straight-line (Haversine) distance to the destination / assumed average
speed. Real traffic and live road conditions are outside the prototype's scope.

## Security notes
Passwords hashed (werkzeug), signed session cookies, role checks on every
endpoint, input validation, secrets from environment variables.

## Deployment
See DEPLOY.md (Render). The simulator runs as a thread inside the app, so always
use a SINGLE worker: `gunicorn -w 1 --threads 4 app:app`.

## Not built yet
Screenshots/diagrams/documentation/defense slides (Phase 13).
