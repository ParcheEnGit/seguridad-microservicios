import React, { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Mail, Plus, RefreshCw, ShieldCheck, Trash2, UserRound, Users, X } from "lucide-react";

import { getRoleLabel } from "../constants/roles.js";
import { authorizeUser, listAuthorizedUsers, revokeUser } from "../services/authApi.js";

const EMPTY_FORM = { name: "", email: "", role: "1" };
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function AddUserModal({ onClose, onCreated }) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event) {
    event.preventDefault();
    const name = form.name.trim();
    const email = form.email.trim().toLowerCase();
    if (name.length < 2) return setError("Ingresa el nombre completo de la persona.");
    if (!EMAIL_PATTERN.test(email)) return setError("Ingresa un correo válido.");
    setSaving(true);
    setError("");
    try {
      await authorizeUser({ name, email, role: Number(form.role) });
      onCreated();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="device-modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="device-modal users-modal" role="dialog" aria-modal="true" aria-labelledby="add-user-title">
        <header className="device-modal__header">
          <div><h1 id="add-user-title">Autorizar usuario</h1><p>Podrá entrar únicamente con este correo mediante Google.</p></div>
          <button type="button" className="device-close" aria-label="Cerrar" onClick={onClose}><X size={20} /></button>
        </header>
        <form className="device-form" onSubmit={submit} noValidate>
          {error && <p className="device-form-error" role="alert">{error}</p>}
          <label>Nombre completo<input required value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} placeholder="Ej. Andrea Yucra" autoComplete="name" /></label>
          <label>Correo autorizado<input required type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} placeholder="persona@ejemplo.com" autoComplete="email" /></label>
          <label>Rol<select value={form.role} onChange={(event) => setForm((current) => ({ ...current, role: event.target.value }))}><option value="1">Lector</option><option value="0">Administrador</option></select></label>
          <p className="users-access-note"><ShieldCheck size={16} /> No se crea contraseña ni acceso público. Google valida la identidad y LabSentinel valida que el correo haya sido autorizado.</p>
          <div className="device-form-actions"><button type="button" className="device-secondary-btn" onClick={onClose}>Cancelar</button><button className="device-primary-btn" disabled={saving}>{saving ? "Autorizando..." : "Autorizar acceso"}</button></div>
        </form>
      </section>
    </div>
  );
}

export function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [notice, setNotice] = useState("");
  const [removingId, setRemovingId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setUsers(await listAuthorizedUsers());
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  function created() {
    setShowModal(false);
    setNotice("Usuario autorizado. Podrá acceder al iniciar sesión con ese correo de Google.");
    load();
  }

  async function removeUser(user) {
    if (!window.confirm(`¿Revocar el acceso de ${user.name}? Ya no podrá iniciar sesión con ${user.email}.`)) return;
    setRemovingId(user.id);
    setError("");
    setNotice("");
    try {
      await revokeUser(user.id);
      setNotice(`Se revocó el acceso de ${user.email}.`);
      await load();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <section className="users-page">
      <header className="devices-header">
        <div><p className="users-page__eyebrow">Control de acceso</p><h1>Administración de usuarios</h1><p>Define quién puede acceder a LabSentinel y con qué rol.</p></div>
        <button type="button" className="device-primary-btn" onClick={() => setShowModal(true)}><Plus size={17} /> Autorizar usuario</button>
      </header>
      <section className="users-info-card"><ShieldCheck size={21} /><p>El acceso por Google está restringido a los correos registrados aquí. Un lector no ve opciones administrativas; un administrador puede gestionar el sistema.</p></section>
      {notice && <p className="users-notice" role="status"><CheckCircle2 size={17} /> {notice}</p>}
      {error && <p className="device-form-error" role="alert">No se pudieron cargar los usuarios: {error}</p>}
      <section className="devices-table-card users-table-card">
        <header className="users-table-card__header"><div><Users size={19} /><strong>Usuarios autorizados</strong><span>{users.length}</span></div><button type="button" className="device-link-btn" onClick={load} disabled={loading}><RefreshCw size={15} /> Actualizar</button></header>
        {loading ? <p className="device-muted">Cargando usuarios...</p> : users.length === 0 ? <div className="device-empty"><UserRound size={28} /><p>Aún no hay usuarios autorizados.</p></div> : <div className="devices-table-wrap"><table><thead><tr><th>Usuario</th><th>Correo autorizado</th><th>Rol</th><th>Estado de Google</th><th aria-label="Acciones" /></tr></thead><tbody>{users.map((user) => <tr key={user.id}><td><strong>{user.name}</strong></td><td><span className="users-email"><Mail size={15} /> {user.email}</span></td><td><span className={`users-role users-role--${user.role === 0 ? "admin" : "reader"}`}>{getRoleLabel(user.role)}</span></td><td><span className={user.google_id ? "users-google users-google--linked" : "users-google"}>{user.google_id ? "Vinculado" : "Pendiente de primer acceso"}</span></td><td><button type="button" className="users-remove-btn" onClick={() => removeUser(user)} disabled={removingId === user.id} aria-label={`Revocar acceso de ${user.name}`} title="Revocar acceso"><Trash2 size={16} /> <span>{removingId === user.id ? "Revocando..." : "Revocar"}</span></button></td></tr>)}</tbody></table></div>}
      </section>
      {showModal && <AddUserModal onClose={() => setShowModal(false)} onCreated={created} />}
    </section>
  );
}
