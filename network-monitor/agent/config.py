import os

# Backend base URL, e.g. https://your-app.up.railway.app
API_BASE_URL = os.environ.get("MONITOR_API_URL", "http://localhost:5000")
API_KEY = os.environ.get("MONITOR_API_KEY", "dev-agent-key-change-me")

# How often the agent collects + sends metrics (seconds)
POLL_INTERVAL = int(os.environ.get("MONITOR_POLL_INTERVAL", 15))

# Host pinged to measure network latency
PING_TARGET = os.environ.get("MONITOR_PING_TARGET", "8.8.8.8")

REQUEST_TIMEOUT = 10  # seconds, for HTTP calls to the backend
