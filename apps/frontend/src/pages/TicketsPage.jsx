import React, { useEffect, useState } from "react";
import { CheckCircle2, ChevronRight, Eye, FileText, Paperclip, Plus, Search, Ticket, UploadCloud, X } from "lucide-react";

import {
  TICKET_ATTACHMENT_MAX_BYTES,
  TICKET_ATTACHMENT_TYPES,
  TICKET_CATEGORIES,
  TICKET_DESCRIPTION_MAX,
  TICKET_DESCRIPTION_MIN,
  TICKET_STATUSES,
  getCategoryLabel,
  getStatusLabel,
} from "../constants/tickets.js";
import { listDevices } from "../services/deviceApi.js";
import { createTicket, getTicket, listMyTickets } from "../services/ticketApi.js";

const REDIRECT_DELAY_MS = 3000;
const EMPTY_FORM = { deviceId: "", category: "", description: "" };

function formatDate(timestamp, withTime = false) {
  return new Intl.DateTimeFormat("es-BO", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(new Date(timestamp));
}

function formatSize(bytes) {
  return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function StatusBadge({ status }) {
  return <span className={`ticket-status ticket-status--${status}`}>{getStatusLabel(status)}</span>;
}

function validateAttachment(file) {
  if (!TICKET_ATTACHMENT_TYPES.includes(file.type)) return "El adjunto debe ser PDF, PNG o JPG.";
  if (file.size > TICKET_ATTACHMENT_MAX_BYTES) return "El adjunto no debe superar 5 MB.";
  return "";
}

function validateForm(form) {
  const errors = {};
  if (!form.deviceId) errors.deviceId = "Selecciona el dispositivo afectado.";
  if (!form.category) errors.category = "Selecciona una categoría.";
  const description = form.description.trim();
  if (!description) errors.description = "Describe la condición observada.";
  else if (description.length < TICKET_DESCRIPTION_MIN) errors.description = `La descripción debe tener al menos ${TICKET_DESCRIPTION_MIN} caracteres.`;
  return errors;
}

function AttachmentPicker({ file, error, onChange }) {
  const [dragging, setDragging] = useState(false);

  function pick(files) {
    const selected = files?.[0];
    if (selected) onChange(selected);
  }

  if (file) {
    return (
      <div className="ticket-attachment-selected">
        <Paperclip size={17} aria-hidden="true" />
        <div><strong>{file.name}</strong><small>{formatSize(file.size)}</small></div>
        <button type="button" aria-label={`Quitar ${file.name}`} onClick={() => onChange(null)}><X size={16} /></button>
      </div>
    );
  }

  return (
    <label
      className={`ticket-dropzone${dragging ? " is-dragging" : ""}${error ? " has-error" : ""}`}
      onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => { event.preventDefault(); setDragging(false); pick(event.dataTransfer.files); }}
    >
      <UploadCloud size={24} aria-hidden="true" />
      <span>Arrastra un archivo o haz clic para seleccionar</span>
      <small>PDF, PNG, JPG (máx. 5 MB)</small>
      <input type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={(event) => { pick(event.target.files); event.target.value = ""; }} />
    </label>
  );
}

function SuccessNotice({ ticket, onView }) {
  return (
    <aside className="ticket-success" role="status" aria-live="polite">
      <div className="ticket-success__card">
        <CheckCircle2 className="ticket-success__icon" size={30} aria-hidden="true" />
        <div>
          <strong>Ticket creado exitosamente</strong>
          <p>Código: {ticket.code}</p>
        </div>
        <small>Redirigiendo a Mis tickets...</small>
        <div className="ticket-success__progress" style={{ animationDuration: `${REDIRECT_DELAY_MS}ms` }} />
        <button type="button" className="device-primary-btn" onClick={onView}>Ver ticket ahora <ChevronRight size={16} /></button>
      </div>
    </aside>
  );
}

function TicketForm({ onCancel, onCreated, onView }) {
  const [devices, setDevices] = useState([]);
  const [devicesError, setDevicesError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [attachment, setAttachment] = useState(null);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [saving, setSaving] = useState(false);
  const [created, setCreated] = useState(null);

  useEffect(() => {
    listDevices({ limit: 100 })
      .then((data) => setDevices(data.items ?? []))
      .catch((requestError) => setDevicesError(requestError.message));
  }, []);

  useEffect(() => {
    if (!created) return undefined;
    const timer = setTimeout(() => onCreated(created), REDIRECT_DELAY_MS);
    return () => clearTimeout(timer);
  }, [created]);

  function change(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  }

  function changeAttachment(file) {
    const attachmentError = file ? validateAttachment(file) : "";
    setErrors((current) => ({ ...current, attachment: attachmentError || undefined }));
    setAttachment(attachmentError ? null : file);
  }

  async function submit(event) {
    event.preventDefault();
    setSubmitError("");
    const nextErrors = validateForm(form);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    setSaving(true);
    try {
      const ticket = await createTicket({ ...form, description: form.description.trim(), attachment });
      setCreated(ticket);
    } catch (requestError) {
      setSubmitError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  const descriptionLength = form.description.trim().length;

  return (
    <section className="tickets-page">
      <nav className="ticket-breadcrumb" aria-label="Ruta de navegación">
        <button type="button" onClick={onCancel}>Tickets</button>
        <ChevronRight size={14} aria-hidden="true" />
        <span>Nuevo ticket</span>
      </nav>
      <header className="devices-header"><div><h1>Crear ticket de incidencia</h1><p>Informa una condición física del equipo que la telemetría no puede detectar.</p></div></header>

      <div className="ticket-create-layout">
        <form className="ticket-form-card" onSubmit={submit} noValidate>
          {submitError && <p className="device-form-error" role="alert">{submitError}</p>}
          {devicesError && <p className="device-form-error" role="alert">No se pudieron cargar los dispositivos: {devicesError}</p>}

          <label className="ticket-field">
            <span>Dispositivo</span>
            <select value={form.deviceId} onChange={(event) => change("deviceId", event.target.value)} aria-invalid={Boolean(errors.deviceId)} disabled={Boolean(created)}>
              <option value="">Seleccione un dispositivo (ej. Router-LAB-01)</option>
              {devices.map((device) => <option key={device.id} value={device.id}>{device.name} · {device.device_code}</option>)}
            </select>
            {errors.deviceId && <small className="ticket-field__error">{errors.deviceId}</small>}
          </label>

          <label className="ticket-field">
            <span>Categoría</span>
            <select value={form.category} onChange={(event) => change("category", event.target.value)} aria-invalid={Boolean(errors.category)} disabled={Boolean(created)}>
              <option value="">Seleccione una opción</option>
              {TICKET_CATEGORIES.map((category) => <option key={category.value} value={category.value}>{category.label}</option>)}
            </select>
            {errors.category && <small className="ticket-field__error">{errors.category}</small>}
          </label>

          <label className="ticket-field">
            <span>Descripción del problema</span>
            <textarea
              rows={5}
              maxLength={TICKET_DESCRIPTION_MAX}
              value={form.description}
              onChange={(event) => change("description", event.target.value)}
              placeholder="Escriba de forma detallada el fallo o síntoma observado en el equipo..."
              aria-invalid={Boolean(errors.description)}
              disabled={Boolean(created)}
            />
            <div className="ticket-field__meta">
              {errors.description ? <small className="ticket-field__error">{errors.description}</small> : <small>Mínimo {TICKET_DESCRIPTION_MIN} caracteres.</small>}
              <small>{descriptionLength}/{TICKET_DESCRIPTION_MAX}</small>
            </div>
          </label>

          <div className="ticket-field">
            <span>Prioridad</span>
            <p className="ticket-priority"><strong>No crítica</strong> Los tickets de lectores son siempre no críticos.</p>
          </div>

          <div className="ticket-field">
            <span>Adjunto (opcional)</span>
            <AttachmentPicker file={attachment} error={errors.attachment} onChange={changeAttachment} />
            {errors.attachment && <small className="ticket-field__error">{errors.attachment}</small>}
          </div>

          <div className="device-form-actions">
            <button type="button" className="ticket-outline-btn" onClick={onCancel}>Cancelar</button>
            <button className="device-primary-btn" disabled={saving || Boolean(created)}>{saving ? "Enviando..." : "Enviar ticket"}</button>
          </div>
        </form>

        {created && <SuccessNotice ticket={created} onView={() => onView(created)} />}
      </div>
    </section>
  );
}

function TicketDetailModal({ ticketId, onClose }) {
  const [ticket, setTicket] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getTicket(ticketId).then(setTicket).catch((requestError) => setError(requestError.message));
  }, [ticketId]);

  return (
    <div className="device-modal-backdrop" role="presentation" onClick={onClose}>
      <section className="device-modal" role="dialog" aria-modal="true" aria-labelledby="ticket-dialog-title" onClick={(event) => event.stopPropagation()}>
        <header className="device-modal__header">
          <div>
            <h1 id="ticket-dialog-title">{ticket ? ticket.code : "Detalle del ticket"}</h1>
            {ticket && <p>{ticket.device_name ?? "Dispositivo no disponible"}{ticket.device_code ? ` · ${ticket.device_code}` : ""}</p>}
          </div>
          <button type="button" onClick={onClose} className="device-close" aria-label="Cerrar ventana"><X size={20} /></button>
        </header>
        <div className="ticket-detail">
          {error && <p className="device-form-error" role="alert">{error}</p>}
          {!ticket && !error && <p className="device-muted">Cargando ticket...</p>}
          {ticket && (
            <>
              <dl className="ticket-detail__grid">
                <div><dt>Estado</dt><dd><StatusBadge status={ticket.status} /></dd></div>
                <div><dt>Categoría</dt><dd>{getCategoryLabel(ticket.category)}</dd></div>
                <div><dt>Prioridad</dt><dd>No crítica</dd></div>
                <div><dt>Registrado</dt><dd>{formatDate(ticket.created_at, true)}</dd></div>
              </dl>
              <h2>Descripción</h2>
              <p className="ticket-detail__description">{ticket.description}</p>
              <h2>Adjunto</h2>
              {ticket.attachment ? (
                <a className="ticket-attachment-link" href={ticket.attachment.url} target="_blank" rel="noreferrer">
                  {ticket.attachment.content_type === "application/pdf" ? <FileText size={17} /> : <Paperclip size={17} />}
                  <span>{ticket.attachment.original_name}</span>
                  <small>{formatSize(ticket.attachment.size_bytes)}</small>
                </a>
              ) : <p className="device-muted">Este ticket no tiene adjunto.</p>}
              {ticket.attachment?.content_type.startsWith("image/") && <img className="ticket-attachment-preview" src={ticket.attachment.url} alt={`Adjunto de ${ticket.code}`} />}
              <h2>Historial</h2>
              <ol className="ticket-history">
                {ticket.history.map((change) => (
                  <li key={change.changed_at}>
                    <div className="ticket-history__change">
                      {change.previous_status && <><StatusBadge status={change.previous_status} /><ChevronRight size={14} aria-hidden="true" /></>}
                      <StatusBadge status={change.new_status} />
                      <small>{formatDate(change.changed_at, true)}</small>
                    </div>
                    {change.note && <p className="ticket-history__note">{change.note}</p>}
                  </li>
                ))}
              </ol>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function TicketList({ onCreate, onView }) {
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const filtered = Boolean(search.trim() || statusFilter);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await listMyTickets({ search: search.trim(), status: statusFilter, limit: 100 });
      setTickets(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = setTimeout(load, search ? 300 : 0);
    return () => clearTimeout(timer);
  }, [search, statusFilter]);

  return (
    <section className="tickets-page">
      <header className="devices-header">
        <div><h1>Mis tickets</h1><p>{total} ticket{total === 1 ? "" : "s"} {filtered ? "encontrado" : "enviado"}{total === 1 ? "" : "s"}</p></div>
        <button type="button" className="ticket-outline-btn ticket-create-btn" onClick={onCreate}><Plus size={17} /> Reportar condición</button>
      </header>

      <section className="ticket-filter-bar" aria-label="Filtros de tickets">
        <label className="device-search"><Search size={17} aria-hidden="true" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Buscar ticket..." /></label>
        <select aria-label="Filtrar por estado" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="">Todos los estados</option>
          {TICKET_STATUSES.map((status) => <option key={status.value} value={status.value}>{status.label}</option>)}
        </select>
      </section>

      {error && (
        <div className="device-form-error ticket-error" role="alert">
          <span>No se pudieron cargar tus tickets: {error}</span>
          <button type="button" className="device-link-btn" onClick={load}>Reintentar</button>
        </div>
      )}

      <section className="devices-table-card ticket-table-card">
        {loading ? <p className="device-muted">Cargando tickets...</p> : tickets.length === 0 ? (
          <div className="device-empty">
            <Ticket size={28} />
            <p>{filtered ? "No se encontraron tickets con esos filtros." : "Aún no registraste tickets."}</p>
            {!filtered && <button type="button" className="device-link-btn" onClick={onCreate}>Reportar una condición</button>}
          </div>
        ) : (
          <>
            <div className="devices-table-wrap">
              <table>
                <thead><tr><th># Ticket</th><th>Dispositivo</th><th>Categoría</th><th>Fecha</th><th>Estado</th><th><span className="sr-only">Acciones</span></th></tr></thead>
                <tbody>
                  {tickets.map((ticket) => (
                    <tr key={ticket.id}>
                      <td><strong>{ticket.code}</strong></td>
                      <td>{ticket.device_name ?? "—"}</td>
                      <td>{getCategoryLabel(ticket.category)}</td>
                      <td>{formatDate(ticket.created_at)}</td>
                      <td><StatusBadge status={ticket.status} /></td>
                      <td><div className="device-actions"><button type="button" title="Ver detalle" aria-label={`Ver detalle de ${ticket.code}`} onClick={() => onView(ticket)}><Eye size={17} /></button></div></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="ticket-mobile-list">
              {tickets.map((ticket) => (
                <button type="button" className="ticket-mobile-card" key={ticket.id} onClick={() => onView(ticket)}>
                  <span className="ticket-mobile-card__top"><small>{ticket.code}</small><StatusBadge status={ticket.status} /></span>
                  <strong>{ticket.device_name ?? "—"}</strong>
                  <span className="ticket-mobile-card__bottom"><span className="ticket-chip">{getCategoryLabel(ticket.category)}</span><small>{formatDate(ticket.created_at)}</small></span>
                </button>
              ))}
            </div>
          </>
        )}
      </section>

      <button type="button" className="device-primary-btn ticket-mobile-create" onClick={onCreate}><Plus size={17} /> Reportar condición</button>
    </section>
  );
}

export function TicketsPage({ initialView = "list" }) {
  const [view, setView] = useState(initialView);
  const [selectedId, setSelectedId] = useState(null);

  return (
    <>
      {view === "create"
        ? <TicketForm onCancel={() => setView("list")} onCreated={() => setView("list")} onView={(ticket) => { setView("list"); setSelectedId(ticket.id); }} />
        : <TicketList onCreate={() => setView("create")} onView={(ticket) => setSelectedId(ticket.id)} />}
      {selectedId && <TicketDetailModal ticketId={selectedId} onClose={() => setSelectedId(null)} />}
    </>
  );
}
