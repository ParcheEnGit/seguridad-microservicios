import React, { useEffect, useState } from "react";
import { Edit3, Eye, Plus, Power, SlidersHorizontal, X } from "lucide-react";
import { canRegisterDevice } from "../constants/roles.js";
import { createDevice, deactivateDevice, listDevices, replaceThresholds, updateDevice } from "../services/deviceApi.js";

const emptyForm = { device_code: "", name: "", device_type: "", location: "", status: "activo", thresholds: [] };

function ThresholdFields({ thresholds, onChange }) {
  function update(index, field, value) { onChange(thresholds.map((item, i) => i === index ? { ...item, [field]: value } : item)); }
  return <div className="device-thresholds">
    <div className="device-section-heading"><span>Umbrales</span><button type="button" className="device-link-btn" onClick={() => onChange([...thresholds, { metric_code: "temperatura", unit: "°C", min_value: "", max_value: "" }])}><Plus size={15}/> Añadir métrica</button></div>
    {thresholds.length === 0 && <p className="device-muted">Sin umbrales configurados.</p>}
    {thresholds.map((threshold, index) => <div className="threshold-row" key={index}>
      <input aria-label="Métrica" value={threshold.metric_code} onChange={(e) => update(index, "metric_code", e.target.value)} placeholder="Métrica" />
      <input aria-label="Unidad" value={threshold.unit} onChange={(e) => update(index, "unit", e.target.value)} placeholder="Unidad" />
      <input aria-label="Valor mínimo" type="number" value={threshold.min_value} onChange={(e) => update(index, "min_value", e.target.value)} placeholder="Mínimo" />
      <input aria-label="Valor máximo" type="number" value={threshold.max_value} onChange={(e) => update(index, "max_value", e.target.value)} placeholder="Máximo" />
      <button type="button" className="device-icon-danger" aria-label="Eliminar umbral" onClick={() => onChange(thresholds.filter((_, i) => i !== index))}><X size={16}/></button>
    </div>)}
  </div>;
}

function DeviceModal({ device, onClose, onSaved }) {
  const [form, setForm] = useState(device ? { ...device, thresholds: device.thresholds.map((t) => ({ ...t, min_value: String(t.min_value), max_value: String(t.max_value) })) } : emptyForm);
  const [error, setError] = useState(""); const [saving, setSaving] = useState(false);
  const change = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  async function submit(event) {
    event.preventDefault(); setError(""); setSaving(true);
    const thresholds = form.thresholds.map(({ metric_code, unit, min_value, max_value }) => ({ metric_code: metric_code.trim().toLowerCase(), unit: unit.trim(), min_value: Number(min_value), max_value: Number(max_value) }));
    try {
      if (device) { const changes = { name: form.name, device_type: form.device_type, location: form.location, status: form.status, metadata: form.metadata ?? {} }; await updateDevice(device.id, changes); await replaceThresholds(device.id, thresholds); }
      else await createDevice({ ...form, device_code: form.device_code.trim().toUpperCase(), thresholds });
      onSaved();
    } catch (requestError) { setError(requestError.message); } finally { setSaving(false); }
  }
  return <div className="device-modal-backdrop" role="presentation"><section className="device-modal" role="dialog" aria-modal="true" aria-labelledby="device-dialog-title">
    <div className="device-modal__header"><div><h1 id="device-dialog-title">{device ? "Editar dispositivo" : "Registrar dispositivo"}</h1><p>Completa la información y los umbrales de monitoreo.</p></div><button onClick={onClose} className="device-close" aria-label="Cerrar"><X/></button></div>
    <form onSubmit={submit} className="device-form">
      {error && <p className="device-form-error">{error}</p>}
      <div className="device-form-grid">
        <label>Código único<input required disabled={Boolean(device)} value={form.device_code} onChange={(e) => change("device_code", e.target.value)} placeholder="LAB-ROUTER-01" /></label>
        <label>Nombre<input required value={form.name} onChange={(e) => change("name", e.target.value)} placeholder="Router de laboratorio" /></label>
        <label>Tipo de dispositivo<input required value={form.device_type} onChange={(e) => change("device_type", e.target.value)} placeholder="Router, sensor, switch..." /></label>
        <label>Ubicación<input required value={form.location} onChange={(e) => change("location", e.target.value)} placeholder="Laboratorio A" /></label>
      </div>
      <ThresholdFields thresholds={form.thresholds} onChange={(thresholds) => change("thresholds", thresholds)} />
      <div className="device-form-actions"><button type="button" className="device-secondary-btn" onClick={onClose}>Cancelar</button><button className="device-primary-btn" disabled={saving}>{saving ? "Guardando..." : "Guardar dispositivo"}</button></div>
    </form>
  </section></div>;
}

export function DevicesPage({ user }) {
  const admin = canRegisterDevice(user.role); const [devices, setDevices] = useState([]); const [selected, setSelected] = useState(null); const [editing, setEditing] = useState(null); const [creating, setCreating] = useState(false); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  async function load() { setLoading(true); setError(""); try { const data = await listDevices(); setDevices(data.items); } catch (requestError) { setError(requestError.message); } finally { setLoading(false); } }
  useEffect(() => { load(); }, []);
  async function deactivate(device) { if (!window.confirm(`¿Desactivar ${device.name}? Se conservará su historial.`)) return; try { await deactivateDevice(device.id); await load(); if (selected?.id === device.id) setSelected(null); } catch (requestError) { setError(requestError.message); } }
  const closeAndReload = async () => { setCreating(false); setEditing(null); await load(); };
  return <section className="devices-page">
    <header className="devices-header"><div><p className="devices-eyebrow">{admin ? "Dashboard Admin" : "Dashboard Lector"}</p><h1>Dispositivos y umbrales</h1><p>Inventario monitoreado y reglas operativas del laboratorio.</p></div>{admin && <button className="device-primary-btn" onClick={() => setCreating(true)}><Plus size={18}/> Registrar dispositivo</button>}</header>
    {error && <p className="device-form-error">{error}</p>}
    <div className="devices-layout"><section className="devices-table-card"><div className="device-section-heading"><span>Inventario ({devices.length})</span><button className="device-link-btn" onClick={load}>Actualizar</button></div>
      {loading ? <p className="device-muted">Cargando dispositivos...</p> : devices.length === 0 ? <div className="device-empty"><SlidersHorizontal size={28}/><p>No existen dispositivos registrados.</p>{admin && <button className="device-link-btn" onClick={() => setCreating(true)}>Registrar el primero</button>}</div> : <div className="devices-table-wrap"><table><thead><tr><th>Dispositivo</th><th>Ubicación</th><th>Estado</th><th>Umbrales</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{devices.map((device) => <tr key={device.id}><td><strong>{device.name}</strong><small>{device.device_code} · {device.device_type}</small></td><td>{device.location}</td><td><span className={`device-status device-status--${device.status}`}>{device.status}</span></td><td>{device.thresholds.length}</td><td className="device-actions"><button title="Ver detalle" onClick={() => setSelected(device)}><Eye size={17}/></button>{admin && <><button title="Editar" onClick={() => setEditing(device)}><Edit3 size={16}/></button>{device.status !== "inactivo" && <button title="Desactivar" className="device-action-danger" onClick={() => deactivate(device)}><Power size={16}/></button>}</>}</td></tr>)}</tbody></table></div>}</section>
      <aside className="device-detail-card">{selected ? <><div className="device-section-heading"><span>Detalle</span><button className="device-link-btn" onClick={() => setSelected(null)}>Cerrar</button></div><h2>{selected.name}</h2><p className="device-muted">{selected.device_code} · {selected.location}</p><dl><dt>Tipo</dt><dd>{selected.device_type}</dd><dt>Estado</dt><dd><span className={`device-status device-status--${selected.status}`}>{selected.status}</span></dd></dl><h3>Umbrales configurados</h3>{selected.thresholds.length ? selected.thresholds.map((t) => <div className="device-threshold-item" key={t.id}><strong>{t.metric_code}</strong><span>{t.min_value} a {t.max_value} {t.unit}</span></div>) : <p className="device-muted">Sin umbrales.</p>}</> : <div className="device-empty"><Eye size={28}/><p>Selecciona un dispositivo para ver su detalle.</p></div>}</aside></div>
    {creating && <DeviceModal onClose={() => setCreating(false)} onSaved={closeAndReload}/>} {editing && <DeviceModal device={editing} onClose={() => setEditing(null)} onSaved={closeAndReload}/>} 
  </section>;
}
