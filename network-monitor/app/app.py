import os
import jwt
import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

from config import Config
from models import db, User, Device, Metric, Alert


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        _seed_admin(app)

    register_routes(app)
    return app


def _seed_admin(app):
    """Create a default admin user on first run if none exists (dev convenience)."""
    if User.query.count() == 0:
        email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("ADMIN_PASSWORD", "changeme123")
        u = User(email=email, role="admin")
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        app.logger.info(f"Seeded default admin user: {email}")


# ---------- Auth helpers ----------

def make_token(user):
    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.datetime.utcnow() + Config.JWT_EXPIRY,
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")


def token_required(f):
    """Protects admin-facing API endpoints. Accepts Bearer JWT from login,
    or falls back to an active dashboard session (so the browser UI works too)."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("user_id"):
            return f(*args, **kwargs)
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            try:
                jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                return f(*args, **kwargs)
            except jwt.PyJWTError:
                pass
        return jsonify({"error": "unauthorized"}), 401
    return wrapper


def agent_key_required(f):
    """Protects the metrics-ingest endpoint. Agents authenticate with a shared API key,
    not a user login — this is a machine-to-machine credential."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-Key", "")
        if key != Config.AGENT_API_KEY:
            return jsonify({"error": "invalid api key"}), 401
        return f(*args, **kwargs)
    return wrapper


# ---------- Alert engine ----------

def evaluate_thresholds(app, device, metric):
    """Simple threshold-based alert logic, per spec section 6."""
    checks = [
        ("high_cpu", metric.cpu_usage, Config.CPU_THRESHOLD, "High CPU usage"),
        ("high_memory", metric.memory_usage, Config.MEMORY_THRESHOLD, "High memory usage"),
        ("low_disk", metric.disk_usage, Config.DISK_THRESHOLD, "Low disk space"),
        ("latency", metric.latency, Config.LATENCY_THRESHOLD, "High network latency"),
    ]
    for alert_type, value, threshold, label in checks:
        if value is None:
            continue
        if value > threshold:
            existing = Alert.query.filter_by(device_id=device.id, alert_type=alert_type, status="active").first()
            if not existing:
                a = Alert(
                    device_id=device.id,
                    alert_type=alert_type,
                    message=f"{label} on {device.hostname}: {value:.1f} (threshold {threshold})",
                    severity="critical" if value > threshold + 5 else "warning",
                    metric_value=value,
                    threshold=threshold,
                )
                db.session.add(a)
        else:
            # value back under threshold -> auto-resolve any active alert of this type
            active = Alert.query.filter_by(device_id=device.id, alert_type=alert_type, status="active").first()
            if active:
                active.status = "resolved"
                active.resolved_at = datetime.datetime.utcnow()
    db.session.commit()


def mark_offline_devices(app):
    """Devices with no metric inside OFFLINE_AFTER get flagged offline + an alert."""
    cutoff = datetime.datetime.utcnow() - Config.OFFLINE_AFTER
    stale = Device.query.filter(Device.last_seen < cutoff, Device.status != "offline").all()
    for d in stale:
        d.status = "offline"
        existing = Alert.query.filter_by(device_id=d.id, alert_type="offline", status="active").first()
        if not existing:
            db.session.add(Alert(
                device_id=d.id, alert_type="offline", severity="critical",
                message=f"{d.hostname} has not reported in over {Config.OFFLINE_AFTER.seconds}s",
            ))
    db.session.commit()


# ---------- Routes ----------

def register_routes(app):

    # ---- API: agent ingest ----
    @app.route("/api/metrics", methods=["POST"])
    @agent_key_required
    def post_metrics():
        data = request.get_json(force=True, silent=True) or {}
        required = ["device_uid", "hostname", "cpu_usage", "memory_usage", "disk_usage"]
        missing = [k for k in required if k not in data]
        if missing:
            return jsonify({"error": f"missing fields: {missing}"}), 400

        device = Device.query.filter_by(device_uid=data["device_uid"]).first()
        if not device:
            device = Device(device_uid=data["device_uid"], hostname=data["hostname"])
            db.session.add(device)

        device.hostname = data.get("hostname", device.hostname)
        device.ip_address = data.get("ip_address", device.ip_address)
        device.operating_system = data.get("operating_system", device.operating_system)
        device.status = "online"
        device.last_seen = datetime.datetime.utcnow()
        db.session.flush()  # ensures device.id is available

        metric = Metric(
            device_id=device.id,
            cpu_usage=data.get("cpu_usage"),
            memory_usage=data.get("memory_usage"),
            disk_usage=data.get("disk_usage"),
            network_in=data.get("network_in"),
            network_out=data.get("network_out"),
            latency=data.get("latency"),
        )
        db.session.add(metric)
        db.session.commit()

        evaluate_thresholds(app, device, metric)
        mark_offline_devices(app)
        return jsonify({"status": "ok"}), 201

    # ---- API: auth ----
    @app.route("/api/auth/login", methods=["POST"])
    def api_login():
        data = request.get_json(force=True, silent=True) or {}
        user = User.query.filter_by(email=data.get("email")).first()
        if not user or not user.check_password(data.get("password", "")):
            return jsonify({"error": "invalid credentials"}), 401
        return jsonify({"token": make_token(user)})

    # ---- API: read endpoints ----
    @app.route("/api/devices", methods=["GET"])
    @token_required
    def api_devices():
        devices = Device.query.all()
        out = []
        for d in devices:
            latest = d.metrics.order_by(Metric.timestamp.desc()).first()
            out.append(d.to_dict(latest))
        return jsonify(out)

    @app.route("/api/devices/<int:device_id>", methods=["GET"])
    @token_required
    def api_device_detail(device_id):
        d = Device.query.get_or_404(device_id)
        latest = d.metrics.order_by(Metric.timestamp.desc()).first()
        return jsonify(d.to_dict(latest))

    @app.route("/api/metrics/<int:device_id>", methods=["GET"])
    @token_required
    def api_metrics_history(device_id):
        limit = int(request.args.get("limit", 50))
        rows = (Metric.query.filter_by(device_id=device_id)
                .order_by(Metric.timestamp.desc()).limit(limit).all())
        return jsonify([m.to_dict() for m in reversed(rows)])

    @app.route("/api/alerts", methods=["GET"])
    @token_required
    def api_alerts():
        status = request.args.get("status")
        q = Alert.query
        if status:
            q = q.filter_by(status=status)
        rows = q.order_by(Alert.created_at.desc()).limit(100).all()
        return jsonify([a.to_dict() for a in rows])

    # ---- Dashboard (session-based) ----
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            user = User.query.filter_by(email=request.form.get("email")).first()
            if user and user.check_password(request.form.get("password", "")):
                session["user_id"] = user.id
                return redirect(url_for("overview"))
            return render_template("login.html", error="Invalid credentials")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    def dashboard_guard():
        return session.get("user_id") is not None

    @app.route("/")
    def overview():
        if not dashboard_guard():
            return redirect(url_for("login"))
        devices = Device.query.all()
        online = sum(1 for d in devices if d.status == "online")
        active_alerts = Alert.query.filter_by(status="active").count()
        return render_template(
            "overview.html", devices=devices, total=len(devices),
            online=online, offline=len(devices) - online, active_alerts=active_alerts,
        )

    @app.route("/devices")
    def devices_page():
        if not dashboard_guard():
            return redirect(url_for("login"))
        devices = Device.query.all()
        rows = [(d, d.metrics.order_by(Metric.timestamp.desc()).first()) for d in devices]
        return render_template("devices.html", rows=rows)

    @app.route("/devices/<int:device_id>")
    def device_detail_page(device_id):
        if not dashboard_guard():
            return redirect(url_for("login"))
        device = Device.query.get_or_404(device_id)
        history = (Metric.query.filter_by(device_id=device_id)
                   .order_by(Metric.timestamp.desc()).limit(50).all())
        return render_template("device_detail.html", device=device, history=list(reversed(history)))

    @app.route("/alerts")
    def alerts_page():
        if not dashboard_guard():
            return redirect(url_for("login"))
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(100).all()
        return render_template("alerts.html", alerts=alerts)


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
