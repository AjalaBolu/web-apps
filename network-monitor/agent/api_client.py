import requests
import config
from logger import get_logger

log = get_logger()


def send_metrics(payload):
    """POSTs the metrics payload to the backend. Returns True on success.
    Failures are logged but never crash the agent — see agent.py's retry loop."""
    url = f"{config.API_BASE_URL}/api/metrics"
    headers = {"X-API-Key": config.API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=config.REQUEST_TIMEOUT)
        if resp.status_code == 201:
            return True
        log.warning(f"Backend rejected metrics: {resp.status_code} {resp.text}")
        return False
    except requests.RequestException as e:
        log.warning(f"Could not reach backend: {e}")
        return False
