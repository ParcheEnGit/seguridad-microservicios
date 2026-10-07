"""Simulador local de lecturas para demostraciones sin hardware físico."""
import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TELEMETRY_URL = os.getenv("TELEMETRY_URL", "http://telemetry-service:8000")
SIMULATOR_KEY = os.environ["SIMULATOR_API_KEY"]
INTERVAL_SECONDS = max(5, int(os.getenv("SIMULATOR_INTERVAL_SECONDS", "15")))
SIMULATOR_ENABLED = os.getenv("SIMULATOR_ENABLED", "true").lower() == "true"


def request_json(path: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(
        f"{TELEMETRY_URL}{path}",
        data=data,
        method=method,
        headers={"X-Simulator-Key": SIMULATOR_KEY, "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=8) as response:
        return json.loads(response.read().decode())


def simulated_value(metric: dict) -> float:
    minimum = metric.get("min_value")
    maximum = metric.get("max_value")
    if minimum is not None and maximum is not None:
        midpoint = (float(minimum) + float(maximum)) / 2
        spread = max((float(maximum) - float(minimum)) * 0.22, 0.2)
        return round(random.uniform(midpoint - spread, midpoint + spread), 2)
    defaults = {"temperatura": (20, 27), "humedad": (45, 65)}
    lower, upper = defaults.get(metric["metric_code"], (1, 100))
    return round(random.uniform(lower, upper), 2)


def send_cycle() -> int:
    targets = request_json("/simulation-targets")
    pending_peaks = request_json("/simulation/peaks")
    peaks_by_metric = {
        (str(peak["device_id"]), peak["metric_code"]): peak
        for peak in pending_peaks
    }
    sent = 0
    for target in targets:
        for metric in target["metrics"]:
            peak = peaks_by_metric.get((str(target["device_id"]), metric["metric_code"]))
            timestamps = [datetime.now(timezone.utc)]
            if target["needs_history"]:
                # Una carga histórica ligera, distribuida durante siete días, mantiene
                # legibles los gráficos de 24 h y de periodos más largos desde la demo.
                now = datetime.now(timezone.utc)
                timestamps = [now - timedelta(hours=hour) for hour in range(7 * 24, 0, -6)] + [now]
            for timestamp in timestamps:
                is_peak_reading = peak is not None and timestamp == timestamps[-1]
                try:
                    request_json(
                        "/readings",
                        method="POST",
                        payload={
                            "device_id": target["device_id"],
                            "metric_code": metric["metric_code"],
                            "unit": metric["unit"],
                            "value": peak["value"] if is_peak_reading else simulated_value(metric),
                            "equipment_status": "operativo",
                            "recorded_at": timestamp.isoformat(),
                        },
                    )
                    sent += 1
                    if is_peak_reading:
                        request_json(f"/simulation/peaks/{peak['id']}/consume", method="POST", payload={})
                        print(
                            f"[PEAK] {target['device_code']} {metric['metric_code']}={peak['value']}{metric['unit']}",
                            flush=True,
                        )
                except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                    print(f"Reading skipped for {target['device_code']}: {exc}", flush=True)
    return sent


def main() -> None:
    print(f"LabSentinel simulator enabled={SIMULATOR_ENABLED}; interval={INTERVAL_SECONDS}s", flush=True)
    while True:
        if not SIMULATOR_ENABLED:
            time.sleep(60)
            continue
        try:
            print(f"Simulator cycle completed: {send_cycle()} readings sent", flush=True)
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print(f"Simulator cycle failed: {exc}", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
