import platform
import socket
import uuid
import psutil


def get_device_uid():
    """Stable ID derived from the machine's MAC address — same every run."""
    return str(uuid.UUID(int=uuid.getnode()))


def get_hostname():
    return socket.gethostname()


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def get_os_info():
    return f"{platform.system()} {platform.release()}"


def collect_system_metrics():
    """CPU/RAM/disk snapshot. cpu_percent needs a short blocking interval to be accurate."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    return cpu, mem, disk


def collect_network_bytes():
    counters = psutil.net_io_counters()
    return counters.bytes_recv, counters.bytes_sent
