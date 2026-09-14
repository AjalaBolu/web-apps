import time
import datetime

import config
import metrics
import network
from api_client import send_metrics
from logger import get_logger

log = get_logger()


def build_payload(prev_net_bytes):
    cpu, mem, disk = metrics.collect_system_metrics()
    recv, sent = metrics.collect_network_bytes()
    latency = network.measure_latency(config.PING_TARGET)

    net_in = net_out = None
    if prev_net_bytes is not None:
        prev_recv, prev_sent = prev_net_bytes
        net_in = max(recv - prev_recv, 0)
        net_out = max(sent - prev_sent, 0)

    payload = {
        "device_uid": metrics.get_device_uid(),
        "hostname": metrics.get_hostname(),
        "ip_address": metrics.get_ip_address(),
        "operating_system": metrics.get_os_info(),
        "cpu_usage": cpu,
        "memory_usage": mem,
        "disk_usage": disk,
        "network_in": net_in,
        "network_out": net_out,
        "latency": latency,
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
    return payload, (recv, sent)


def run():
    log.info(f"Starting monitoring agent — reporting to {config.API_BASE_URL} every {config.POLL_INTERVAL}s")
    prev_net_bytes = None
    while True:
        try:
            payload, prev_net_bytes = build_payload(prev_net_bytes)
            ok = send_metrics(payload)
            log.info(f"Sent metrics ({'ok' if ok else 'failed'}): CPU {payload['cpu_usage']}% "
                      f"RAM {payload['memory_usage']}% Disk {payload['disk_usage']}%")
        except Exception as e:
            # Catch-all so one bad reading never kills the agent process (spec 10.7)
            log.error(f"Unexpected error in agent loop: {e}")
        time.sleep(config.POLL_INTERVAL)


if __name__ == "__main__":
    run()
