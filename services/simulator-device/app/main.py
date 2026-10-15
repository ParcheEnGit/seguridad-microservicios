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
RARE_PEAK_PROBABILITY = min(0.05, max(0.0, float(os.getenv("SIMULATOR_RARE_PEAK_PROBABILITY", "0.00005"))))

# Perfil SNMP v2c emulado: conserva OID y versión en cada lectura para que la
# integración con agentes físicos pueda sustituir al simulador sin cambiar el
# contrato de telemetría.
SNMP_OIDS = {
    "temperatura": "1.3.6.1.4.1.53864.1.1.1.0",
    "humedad": "1.3.6.1.4.1.53864.1.1.2.0",
}


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


def rare_peak_value(metric: dict) -> tuple[float, str] | None:
    """Genera anomalías críticas excepcionales solo donde existe un umbral."""
    if not metric.get("has_threshold") or random.random() >= RARE_PEAK_PROBABILITY:
        return None
    minimum = float(metric["min_value"])
    maximum = float(metric["max_value"])
    margin = max((maximum - minimum) * random.uniform(0.25, 0.55), 0.5)
    return (
        round(maximum + margin, 2) if random.choice((True, False)) else round(minimum - margin, 2),
        "pico_aleatorio",
    )


def snmp_payload(metric: dict, event: str) -> dict:
    return {
        "protocol": "SNMP",
        "snmp_version": "v2c",
        "oid": SNMP_OIDS.get(metric["metric_code"], "1.3.6.1.4.1.53864.1.1.255.0"),
        "transport": "simulado",
        "simulation_event": event,
    }


def send_cycle() -> tuple[int, dict[str, list[str]], int]:
    targets = request_json("/simulation-targets")
    pending_peaks = request_json("/simulation/peaks")
    peaks_by_metric = {
        (str(peak["device_id"]), peak["metric_code"]): peak
        for peak in pending_peaks
    }
    sent = 0
    current_readings: dict[str, list[str]] = {}
    history_readings = 0
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
                is_current_reading = timestamp == timestamps[-1]
                is_peak_reading = peak is not None and is_current_reading
                random_peak = rare_peak_value(metric) if is_current_reading and not is_peak_reading else None
                event = "pico_forzado" if is_peak_reading else (random_peak[1] if random_peak else "normal")
                value = peak["value"] if is_peak_reading else (random_peak[0] if random_peak else simulated_value(metric))
                try:
                    result = request_json(
                        "/readings",
                        method="POST",
                        payload={
                            "device_id": target["device_id"],
                            "metric_code": metric["metric_code"],
                            "unit": metric["unit"],
                            "value": value,
                            "equipment_status": "operativo",
                            "recorded_at": timestamp.isoformat(),
                            "payload": snmp_payload(metric, event),
                        },
                    )
                    sent += 1
                    if is_current_reading:
                        kind = "PICO FORZADO" if is_peak_reading else ("PICO ALEATORIO" if random_peak else "normal")
                        alert = " · ALERTA" if result.get("out_of_range") else ""
                        current_readings.setdefault(target["device_code"], []).append(
                            f"SNMP {metric['metric_code']}={value} {metric['unit']} ({kind}{alert})"
                        )
                    else:
                        history_readings += 1
                    if is_peak_reading:
                        request_json(f"/simulation/peaks/{peak['id']}/consume", method="POST", payload={})
                except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                    print(f"[ERROR] Lectura no enviada para {target['device_code']}: {exc}", flush=True)
    return sent, current_readings, history_readings


def main() -> None:
    state = "activo" if SIMULATOR_ENABLED else "desactivado"
    print(
        f"LabSentinel | Simulador SNMP v2c {state} | Intervalo: {INTERVAL_SECONDS} s | Pico aleatorio: {RARE_PEAK_PROBABILITY:.4%}",
        flush=True,
    )
    while True:
        if not SIMULATOR_ENABLED:
            time.sleep(60)
            continue
        try:
            sent, current_readings, history_readings = send_cycle()
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"[CICLO {timestamp}] {sent} lecturas enviadas para "
                f"{len(current_readings)} dispositivo(s)",
                flush=True,
            )
            for device_code, readings in current_readings.items():
                print(f"  └─ {device_code}: {' | '.join(readings)}", flush=True)
            if history_readings:
                print(
                    f"  └─ Historial inicial: {history_readings} lecturas distribuidas en 7 días.",
                    flush=True,
                )
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            print(f"[ERROR] El ciclo de simulación falló: {exc}", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
