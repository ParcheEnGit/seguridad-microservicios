import React, { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, ArrowLeft, Radio, ShieldCheck, Zap } from "lucide-react";

import { listDevices } from "../services/deviceApi.js";
import { createSimulationPeak } from "../services/telemetryApi.js";

const METRIC_LABELS = { temperatura: "Temperatura", humedad: "Humedad" };

export function PeakControlPage() {
  const [devices, setDevices] = useState([]);
  const [deviceId, setDeviceId] = useState("");
  const [metric, setMetric] = useState("temperatura");
  const [direction, setDirection] = useState("alto");
  const [cycles, setCycles] = useState(3);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    let mounted = true;
    listDevices({ limit: 100, status: "activo" })
      .then((response) => {
        if (!mounted) return;
        const simulatable = (response.items ?? []).filter((device) => device.thresholds?.some((threshold) => ["temperatura", "humedad"].includes(threshold.metric_code)));
        setDevices(simulatable);
        setDeviceId(simulatable[0]?.id ?? "");
      })
      .catch((requestError) => mounted && setError(requestError.message))
      .finally(() => mounted && setLoading(false));
    return () => { mounted = false; };
  }, []);

  const selected = useMemo(() => devices.find((device) => device.id === deviceId), [devices, deviceId]);
  const availableMetrics = selected?.thresholds?.filter((threshold) => ["temperatura", "humedad"].includes(threshold.metric_code)) ?? [];

  useEffect(() => {
    if (availableMetrics.length && !availableMetrics.some((threshold) => threshold.metric_code === metric)) setMetric(availableMetrics[0].metric_code);
  }, [availableMetrics, metric]);

  async function submit(event) {
    event.preventDefault();
    if (!deviceId) return;
    setSending(true);
    setError("");
    setResult(null);
    try {
      setResult(await createSimulationPeak({ device_id: deviceId, metric_code: metric, direction, cycles: Number(cycles) }));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="peak-page">
      <div className="peak-page__matrix" aria-hidden="true" />
      <section className="peak-terminal">
        <div className="peak-terminal__bar"><span>labsentinel@simulator:~$</span><span><i /> ENLACE SEGURO · ADMIN</span></div>
        <header className="peak-terminal__header">
          <div><p>./simulatorctl --modo demostración</p><h1><Radio size={22} /> Control de picos</h1><span>CANAL: SIMULADOR AUTORIZADO · ESTADO: EN ESPERA</span></div>
          <button type="button" onClick={() => window.location.assign("/")}><ArrowLeft size={16} /> dashboard</button>
        </header>

        <section className="peak-terminal__notice"><ShieldCheck size={17} /><p><b>AVISO:</b> se programará una lectura fuera de umbral. El simulador la emitirá en su próximo ciclo; el historial no se modifica.</p></section>

        <form className="peak-terminal__form" onSubmit={submit}>
          <label><span className="peak-terminal__field-label">01 / objetivo</span><select value={deviceId} disabled={loading || !devices.length} onChange={(event) => setDeviceId(event.target.value)}>{devices.length === 0 && <option value="">No hay dispositivos activos con umbrales</option>}{devices.map((device) => <option key={device.id} value={device.id}>{device.name} · {device.device_code}</option>)}</select></label>
          <div className="peak-terminal__options">
            <fieldset><legend>02 / métrica</legend>{availableMetrics.map((threshold) => <label key={threshold.metric_code}><input type="radio" name="metric" checked={metric === threshold.metric_code} onChange={() => setMetric(threshold.metric_code)} /> {METRIC_LABELS[threshold.metric_code]} <small>{threshold.min_value}–{threshold.max_value} {threshold.unit}</small></label>)}</fieldset>
            <fieldset><legend>03 / dirección</legend><label><input type="radio" name="direction" checked={direction === "alto"} onChange={() => setDirection("alto")} /> pico elevado</label><label><input type="radio" name="direction" checked={direction === "bajo"} onChange={() => setDirection("bajo")} /> pico bajo</label></fieldset>
            <label><span className="peak-terminal__field-label">04 / duración</span><select value={cycles} onChange={(event) => setCycles(event.target.value)}>{[1, 2, 3, 5, 8, 10].map((value) => <option key={value} value={value}>{value} ciclo{value === 1 ? "" : "s"}</option>)}</select></label>
          </div>
          {error && <p className="peak-terminal__error"><AlertTriangle size={16} /> {error}</p>}
          {result && <p className="peak-terminal__success"><Activity size={16} /> Programado: {result.device_code} / {METRIC_LABELS[result.metric_code]} = {result.value} {result.unit}, durante {result.cycles_remaining} ciclos.</p>}
          <p className="peak-terminal__command">$ queue_peak --metric={metric} --direction={direction} --cycles={cycles}</p>
          <button className="peak-terminal__trigger" disabled={loading || sending || !deviceId}><Zap size={17} /> {sending ? "programando..." : "ejecutar pico"}</button>
        </form>
        <footer><span>ruta directa: <code>/peak</code></span><span>demostración local controlada</span></footer>
      </section>
    </main>
  );
}
