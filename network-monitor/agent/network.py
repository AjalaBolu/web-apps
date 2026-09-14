import subprocess
import platform
import re


def measure_latency(target):
    """Pings the target once and returns round-trip time in ms, or None if unreachable.
    Uses the system ping command so no extra Python dependency is required."""
    count_flag = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        result = subprocess.run(
            ["ping", count_flag, "1", target],
            capture_output=True, text=True, timeout=5,
        )
        match = re.search(r"time[=<]([\d.]+)", result.stdout)
        return float(match.group(1)) if match else None
    except (subprocess.SubprocessError, OSError):
        return None
