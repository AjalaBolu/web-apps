import os
from datetime import timedelta

class Config:
    # Never hardcode secrets — pull from environment variables at deploy time.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///local_dev.db"
    ).replace("postgres://", "postgresql://", 1)  # Railway/Render give old-style URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API key agents must send in the X-API-Key header
    AGENT_API_KEY = os.environ.get("AGENT_API_KEY", "dev-agent-key-change-me")

    # Alert thresholds — kept configurable per section 7/6 of the spec
    CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", 90))
    MEMORY_THRESHOLD = float(os.environ.get("MEMORY_THRESHOLD", 90))
    DISK_THRESHOLD = float(os.environ.get("DISK_THRESHOLD", 90))
    LATENCY_THRESHOLD = float(os.environ.get("LATENCY_THRESHOLD", 200))  # ms

    # A device with no metric in this window is marked offline
    OFFLINE_AFTER = timedelta(seconds=int(os.environ.get("OFFLINE_AFTER_SECONDS", 90)))

    JWT_EXPIRY = timedelta(hours=12)
