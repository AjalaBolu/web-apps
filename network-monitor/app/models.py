from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Device(db.Model):
    __tablename__ = "devices"
    id = db.Column(db.Integer, primary_key=True)
    device_uid = db.Column(db.String(64), unique=True, nullable=False)  # stable id agent sends
    hostname = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(64))
    operating_system = db.Column(db.String(120))
    status = db.Column(db.String(20), default="unknown")  # online / offline / unknown
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    metrics = db.relationship("Metric", backref="device", lazy="dynamic", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", backref="device", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self, latest_metric=None):
        return {
            "id": self.id,
            "device_uid": self.device_uid,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "operating_system": self.operating_system,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "latest": latest_metric.to_dict() if latest_metric else None,
        }


class Metric(db.Model):
    __tablename__ = "metrics"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    network_in = db.Column(db.Float)
    network_out = db.Column(db.Float)
    latency = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "network_in": self.network_in,
            "network_out": self.network_out,
            "latency": self.latency,
            "timestamp": self.timestamp.isoformat(),
        }


class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False)  # high_cpu, high_memory, low_disk, offline, latency
    message = db.Column(db.String(255))
    severity = db.Column(db.String(20), default="warning")  # warning / critical
    metric_value = db.Column(db.Float)
    threshold = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="active")  # active / resolved

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "device_hostname": self.device.hostname if self.device else None,
            "alert_type": self.alert_type,
            "message": self.message,
            "severity": self.severity,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "status": self.status,
        }
