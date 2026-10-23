
import React, { useEffect, useState } from "react";
import { Bell, Monitor, Ticket } from "lucide-react";

import {
  getDeviceReport,
  getAlertReport,
  getTicketReport,
} from "../services/reportApi.js";

import { listDevices } from "../services/deviceApi.js";

import ReportTimelineChart from "../components/reports/ReportTimelineChart.jsx";

// HU11: Tipos de reportes administrativos.
const REPORT_TABS = [
  { id: "devices", label: "Dispositivos", icon: Monitor },
  { id: "alerts", label: "Alertas", icon: Bell },
  { id: "tickets", label: "Tickets", icon: Ticket },
];

const contentStyle = {
  padding: "24px",
  boxSizing: "border-box",
  minWidth: 0,
};

const filtersStyle = {
  display: "flex",
  flexWrap: "wrap",
  alignItems: "flex-end",
  gap: "16px",
  marginBottom: "28px",
};

const filterStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "8px",
  minWidth: "170px",
  flex: "1 1 170px",
  fontWeight: 500,
};

const inputStyle = {
  width: "100%",
  minHeight: "44px",
  padding: "10px 12px",
  border: "1px solid #cbd5e1",
  borderRadius: "8px",
  background: "#ffffff",
  color: "#334155",
  fontSize: "14px",
  boxSizing: "border-box",
};

const statsStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))",
  gap: "16px",
  marginBottom: "30px",
};

const statStyle = {
  padding: "20px",
  border: "1px solid #e2e8f0",
  borderRadius: "16px",
  background: "#ffffff",
  boxShadow: "0 6px 20px rgba(15, 23, 42, 0.04)",
};

const cellStyle = {
  padding: "14px 16px",
  borderBottom: "1px solid #e2e8f0",
  verticalAlign: "top",
};

const headingStyle = {
  ...cellStyle,
  color: "#475569",
  background: "#f8fafc",
  fontWeight: 600,
  whiteSpace: "nowrap",
};

const sectionTitleStyle = {
  margin: "0 0 16px",
};

const emptyStyle = {
  padding: "24px",
  textAlign: "center",
  color: "#64748b",
};

// Fecha actual del navegador en horario local.
function getTodayDate() {
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

// Primer día del mes actual.
function getFirstDayOfMonth() {
  return `${getTodayDate().slice(0, 7)}-01`;
}

// Formato de fechas para las tablas.
function formatDate(value) {
  if (!value) return "Sin fecha";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Fecha no válida";
  }

  return date.toLocaleDateString("es-BO");
}

// Formato legible de estados y categorías.
function formatStatus(value) {
  if (!value) return "Sin estado";

  return String(value)
    .replaceAll("_", " ")
    .replace(/^./, (letter) => letter.toUpperCase());
}

// Tarjetas de indicadores.
function ReportStat({ title, value }) {
  return (
    <div style={statStyle}>
      <h3
        style={{
          margin: "0 0 14px",
          fontSize: "15px",
          fontWeight: 600,
          color: "#475569",
        }}
      >
        {title}
      </h3>

      <p
        style={{
          margin: 0,
          fontSize: "28px",
          fontWeight: 700,
          color: "#064e3b",
        }}
      >
        {value ?? 0}
      </p>
    </div>
  );
}

// Tabla reutilizable para los tres reportes.
function ReportTable({
  headings,
  children,
  empty,
  emptyMessage,
}) {
  return (
    <div
      style={{
        border: "1px solid #e2e8f0",
        borderRadius: "12px",
        overflow: "hidden",
        background: "#ffffff",
      }}
    >
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            textAlign: "left",
          }}
        >
          <thead>
            <tr>
              {headings.map((heading) => (
                <th key={heading} scope="col" style={headingStyle}>
                  {heading}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>{children}</tbody>
        </table>
      </div>

      {empty && (
        <p style={emptyStyle}>
          {emptyMessage}
        </p>
      )}
    </div>
  );
}

// Filtros de fecha: no permiten seleccionar fechas futuras.
function DateFilters({
  startDate,
  endDate,
  setStartDate,
  setEndDate,
  today,
}) {
  return (
    <>
      <label style={filterStyle}>
        Fecha inicial

        <input
          type="date"
          value={startDate}
          max={endDate < today ? endDate : today}
          onChange={(event) => {
            const newDate = event.target.value;
            const currentToday = getTodayDate();

            if (
              newDate &&
              newDate <= currentToday &&
              newDate <= endDate
            ) {
              setStartDate(newDate);
            }
          }}
          style={inputStyle}
        />
      </label>

      <label style={filterStyle}>
        Fecha final

        <input
          type="date"
          value={endDate}
          min={startDate}
          max={today}
          onChange={(event) => {
            const newDate = event.target.value;
            const currentToday = getTodayDate();

            if (
              newDate &&
              newDate >= startDate &&
              newDate <= currentToday
            ) {
              setEndDate(newDate);
            }
          }}
          style={inputStyle}
        />
      </label>
    </>
  );
}

// Selector de dispositivo compartido.
function DeviceFilter({
  value,
  onChange,
  availableDevices,
}) {
  return (
    <label style={filterStyle}>
      Dispositivo

      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={inputStyle}
      >
        <option value="">
          Todos los dispositivos
        </option>

        {availableDevices.map((device) => (
          <option key={device.id} value={device.id}>
            {device.device_code} - {device.name}
          </option>
        ))}
      </select>
    </label>
  );
}

// Selector reutilizable para estados, severidad y categoría.
function SelectFilter({
  label,
  value,
  onChange,
  options,
}) {
  return (
    <label style={filterStyle}>
      {label}

      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={inputStyle}
      >
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
          >
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

// Mensajes de carga y errores.
function ReportMessage({
  loading,
  error,
  label,
}) {
  if (loading) {
    return (
      <p
        role="status"
        style={{
          padding: "16px",
          color: "#475569",
          background: "#f8fafc",
          borderRadius: "8px",
        }}
      >
        Cargando reporte de {label}...
      </p>
    );
  }

  if (error) {
    return (
      <p
        role="alert"
        style={{
          padding: "16px",
          color: "#b91c1c",
          background: "#fef2f2",
          borderRadius: "8px",
        }}
      >
        No se pudo cargar el reporte: {error}
      </p>
    );
  }

  return null;
}

// HU11: Página principal de reportes administrativos.
export function ReportsPage() {
  const [activeTab, setActiveTab] = useState("devices");

  // Fechas compartidas.
  const [today, setToday] = useState(getTodayDate);
  const [startDate, setStartDate] = useState(getFirstDayOfMonth);
  const [endDate, setEndDate] = useState(getTodayDate);

  // Dispositivos disponibles.
  const [selectedDevice, setSelectedDevice] = useState("");
  const [availableDevices, setAvailableDevices] = useState([]);
  const [devicesError, setDevicesError] = useState("");

  // Reporte de dispositivos.
  const [selectedStatus, setSelectedStatus] = useState("");
  const [deviceReport, setDeviceReport] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Reporte de alertas.
  const [alertSeverity, setAlertSeverity] = useState("");
  const [alertStatus, setAlertStatus] = useState("");
  const [alertReport, setAlertReport] = useState(null);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [alertsError, setAlertsError] = useState(null);

  // Reporte de tickets.
  const [ticketStatus, setTicketStatus] = useState("");
  const [ticketCategory, setTicketCategory] = useState("");
  const [ticketReport, setTicketReport] = useState(null);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [ticketsError, setTicketsError] = useState(null);

  // Mantener actualizada la fecha máxima.
  useEffect(() => {
    function updateToday() {
      const currentToday = getTodayDate();

      setToday(currentToday);

      setEndDate((previousDate) =>
        previousDate > currentToday
          ? currentToday
          : previousDate
      );

      setStartDate((previousDate) =>
        previousDate > currentToday
          ? currentToday
          : previousDate
      );
    }

    updateToday();

    const intervalId = window.setInterval(updateToday, 60000);
    window.addEventListener("focus", updateToday);

    return () => {
      window.clearInterval(intervalId);
      window.removeEventListener("focus", updateToday);
    };
  }, []);

  // Obtener dispositivos para los filtros.
  useEffect(() => {
    let cancelled = false;

    async function loadDevices() {
      try {
        const response = await listDevices();

        if (!cancelled) {
          setAvailableDevices(response.items ?? []);
          setDevicesError("");
        }
      } catch {
        if (!cancelled) {
          setAvailableDevices([]);
          setDevicesError(
            "No se pudo cargar la lista de dispositivos."
          );
        }
      }
    }

    loadDevices();

    return () => {
      cancelled = true;
    };
  }, []);

  // Consultar reporte de dispositivos.
  useEffect(() => {
    if (activeTab !== "devices") {
      return undefined;
    }

    let cancelled = false;

    async function loadDeviceReport() {
      setIsLoading(true);
      setError(null);

      try {
        const data = await getDeviceReport({
          startDate,
          endDate,
          deviceId: selectedDevice,
          status: selectedStatus,
        });

        if (!cancelled) {
          setDeviceReport(data);
        }
      } catch (err) {
        if (!cancelled) {
          setDeviceReport(null);
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadDeviceReport();

    return () => {
      cancelled = true;
    };
  }, [
    activeTab,
    startDate,
    endDate,
    selectedDevice,
    selectedStatus,
  ]);

  // Consultar reporte de alertas.
  useEffect(() => {
    if (activeTab !== "alerts") {
      return undefined;
    }

    let cancelled = false;

    async function loadAlertReport() {
      setAlertsLoading(true);
      setAlertsError(null);

      try {
        const data = await getAlertReport({
          startDate,
          endDate,
          deviceId: selectedDevice,
          severity: alertSeverity,
          status: alertStatus,
        });

        if (!cancelled) {
          setAlertReport(data);
        }
      } catch (err) {
        if (!cancelled) {
          setAlertReport(null);
          setAlertsError(err.message);
        }
      } finally {
        if (!cancelled) {
          setAlertsLoading(false);
        }
      }
    }

    loadAlertReport();

    return () => {
      cancelled = true;
    };
  }, [
    activeTab,
    startDate,
    endDate,
    selectedDevice,
    alertSeverity,
    alertStatus,
  ]);

  // Consultar reporte de tickets.
  useEffect(() => {
    if (activeTab !== "tickets") {
      return undefined;
    }

    let cancelled = false;

    async function loadTicketReport() {
      setTicketsLoading(true);
      setTicketsError(null);

      try {
        const data = await getTicketReport({
          startDate,
          endDate,
          deviceId: selectedDevice,
          status: ticketStatus,
          category: ticketCategory,
        });

        if (!cancelled) {
          setTicketReport(data);
        }
      } catch (err) {
        if (!cancelled) {
          setTicketReport(null);
          setTicketsError(err.message);
        }
      } finally {
        if (!cancelled) {
          setTicketsLoading(false);
        }
      }
    }

    loadTicketReport();

    return () => {
      cancelled = true;
    };
  }, [
    activeTab,
    startDate,
    endDate,
    selectedDevice,
    ticketStatus,
    ticketCategory,
  ]);

  const currentTab =
    REPORT_TABS.find((tab) => tab.id === activeTab) ??
    REPORT_TABS[0];

  const dateFilterProps = {
    startDate,
    endDate,
    setStartDate,
    setEndDate,
    today,
  };

  const deviceFilterProps = {
    value: selectedDevice,
    onChange: setSelectedDevice,
    availableDevices,
  };

  return (
    <main className="reader-dashboard">
      <header className="reader-dashboard__header">
        <p className="reader-dashboard__eyebrow">
          Administración
        </p>

        <h1>Reportes administrativos</h1>

        <p className="reader-dashboard__subtitle">
          Consulta de información histórica de dispositivos,
          alertas y tickets del laboratorio.
        </p>
      </header>

      <section
        className="reader-panel"
        style={{ overflow: "hidden" }}
      >
        {/* Navegación entre reportes */}
        <div
          role="tablist"
          aria-label="Tipos de reportes"
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "12px",
            padding: "20px 24px",
            borderBottom: "1px solid #e2e8f0",
          }}
        >
          {REPORT_TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={activeTab === id}
              onClick={() => setActiveTab(id)}
              className={
                activeTab === id
                  ? "ticket-outline-btn"
                  : "reader-panel__link"
              }
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "12px 16px",
                cursor: "pointer",
              }}
            >
              <Icon size={18} aria-hidden="true" />
              {label}
            </button>
          ))}
        </div>

        <div role="tabpanel">
          <div
            style={{
              padding: "24px 24px 12px",
              borderBottom: "1px solid #e2e8f0",
            }}
          >
            <h2 style={{ margin: "0 0 8px" }}>
              Reporte de {currentTab.label.toLowerCase()}
            </h2>

            <p style={{ margin: "0 0 12px" }}>
              Consulta los filtros, indicadores, gráficos
              históricos y registros del reporte seleccionado.
            </p>
          </div>

          <div style={contentStyle}>

            {/* REPORTE DE DISPOSITIVOS */}
            {activeTab === "devices" && (
              <div>
                <div style={filtersStyle}>
                  <DateFilters {...dateFilterProps} />

                  <DeviceFilter {...deviceFilterProps} />

                  <SelectFilter
                    label="Estado"
                    value={selectedStatus}
                    onChange={setSelectedStatus}
                    options={[
                      {
                        value: "",
                        label: "Todos los estados",
                      },
                      {
                        value: "activo",
                        label: "Activo",
                      },
                      {
                        value: "inactivo",
                        label: "Inactivo",
                      },
                      {
                        value: "mantenimiento",
                        label: "Mantenimiento",
                      },
                    ]}
                  />
                </div>

                {devicesError && (
                  <p
                    role="alert"
                    style={{ color: "#b91c1c" }}
                  >
                    {devicesError}
                  </p>
                )}

                <ReportMessage
                  loading={isLoading}
                  error={error}
                  label="dispositivos"
                />

                {!isLoading && !error && deviceReport && (
                  <>
                    <div style={statsStyle}>
                      <ReportStat
                        title="Total de dispositivos"
                        value={deviceReport.summary.total}
                      />

                      <ReportStat
                        title="Activos"
                        value={deviceReport.summary.activos}
                      />

                      <ReportStat
                        title="Inactivos"
                        value={deviceReport.summary.inactivos}
                      />

                      <ReportStat
                        title="En mantenimiento"
                        value={
                          deviceReport.summary.mantenimiento
                        }
                      />
                    </div>

                    {/* HU11: Gráfico histórico de dispositivos */}
                    <ReportTimelineChart
                      type="devices"
                      timeline={deviceReport.timeline}
                      title="Histórico de dispositivos registrados"
                    />

                    <h3 style={sectionTitleStyle}>
                      Detalle de dispositivos
                    </h3>

                    <ReportTable
                      headings={[
                        "Código",
                        "Nombre",
                        "Tipo",
                        "Ubicación",
                        "Estado",
                        "Fecha de registro",
                      ]}
                      empty={
                        (deviceReport.devices ?? []).length === 0
                      }
                      emptyMessage="No se encontraron dispositivos con los filtros seleccionados."
                    >
                      {(deviceReport.devices ?? []).map((device) => (
                        <tr key={device.id}>
                          <td style={cellStyle}>
                            {device.device_code}
                          </td>

                          <td style={cellStyle}>
                            {device.name}
                          </td>

                          <td style={cellStyle}>
                            {device.device_type}
                          </td>

                          <td style={cellStyle}>
                            {device.location || "Sin ubicación"}
                          </td>

                          <td style={cellStyle}>
                            {formatStatus(device.status)}
                          </td>

                          <td style={cellStyle}>
                            {formatDate(device.created_at)}
                          </td>
                        </tr>
                      ))}
                    </ReportTable>
                  </>
                )}
              </div>
            )}

            {/* REPORTE DE ALERTAS */}
            {activeTab === "alerts" && (
              <div>
                <div style={filtersStyle}>
                  <DateFilters {...dateFilterProps} />

                  <DeviceFilter {...deviceFilterProps} />

                  <SelectFilter
                    label="Severidad"
                    value={alertSeverity}
                    onChange={setAlertSeverity}
                    options={[
                      {
                        value: "",
                        label: "Todas las severidades",
                      },
                      {
                        value: "critica",
                        label: "Crítica",
                      },
                      {
                        value: "advertencia",
                        label: "Advertencia",
                      },
                    ]}
                  />

                  <SelectFilter
                    label="Estado"
                    value={alertStatus}
                    onChange={setAlertStatus}
                    options={[
                      {
                        value: "",
                        label: "Todos los estados",
                      },
                      {
                        value: "abierta",
                        label: "Abierta",
                      },
                      {
                        value: "revisada",
                        label: "Revisada",
                      },
                      {
                        value: "cerrada",
                        label: "Cerrada",
                      },
                    ]}
                  />
                </div>

                {devicesError && (
                  <p
                    role="alert"
                    style={{ color: "#b91c1c" }}
                  >
                    {devicesError}
                  </p>
                )}

                <ReportMessage
                  loading={alertsLoading}
                  error={alertsError}
                  label="alertas"
                />

                {!alertsLoading &&
                  !alertsError &&
                  alertReport && (
                    <>
                      <div style={statsStyle}>
                        <ReportStat
                          title="Total de alertas"
                          value={alertReport.summary.total}
                        />

                        <ReportStat
                          title="Críticas"
                          value={alertReport.summary.criticas}
                        />

                        <ReportStat
                          title="Advertencias"
                          value={
                            alertReport.summary.advertencias
                          }
                        />

                        <ReportStat
                          title="Abiertas"
                          value={alertReport.summary.abiertas}
                        />

                        <ReportStat
                          title="Revisadas"
                          value={alertReport.summary.revisadas}
                        />

                        <ReportStat
                          title="Cerradas"
                          value={alertReport.summary.cerradas}
                        />
                      </div>

                      {/* HU11: Gráfico histórico de alertas */}
                      <ReportTimelineChart
                        type="alerts"
                        timeline={alertReport.timeline}
                        title="Histórico de alertas por severidad"
                      />

                      <h3 style={sectionTitleStyle}>
                        Detalle de alertas
                      </h3>

                      <ReportTable
                        headings={[
                          "Dispositivo",
                          "Métrica",
                          "Valor",
                          "Severidad",
                          "Estado",
                          "Fecha de creación",
                        ]}
                        empty={
                          (alertReport.alerts ?? []).length === 0
                        }
                        emptyMessage="No se encontraron alertas con los filtros seleccionados."
                      >
                        {(alertReport.alerts ?? []).map((alert) => (
                          <tr key={alert.id}>
                            <td style={cellStyle}>
                              {alert.device_name ||
                                alert.device_code ||
                                "Sin dispositivo"}
                            </td>

                            <td style={cellStyle}>
                              {alert.metric_code}
                            </td>

                            <td style={cellStyle}>
                              {alert.value} {alert.unit}
                            </td>

                            <td style={cellStyle}>
                              {formatStatus(alert.severity)}
                            </td>

                            <td style={cellStyle}>
                              {formatStatus(alert.status)}
                            </td>

                            <td style={cellStyle}>
                              {formatDate(alert.created_at)}
                            </td>
                          </tr>
                        ))}
                      </ReportTable>
                    </>
                  )}
              </div>
            )}

            {/* REPORTE DE TICKETS */}
            {activeTab === "tickets" && (
              <div>
                <div style={filtersStyle}>
                  <DateFilters {...dateFilterProps} />

                  <DeviceFilter {...deviceFilterProps} />

                  <SelectFilter
                    label="Estado"
                    value={ticketStatus}
                    onChange={setTicketStatus}
                    options={[
                      {
                        value: "",
                        label: "Todos los estados",
                      },
                      {
                        value: "abierto",
                        label: "Abierto",
                      },
                      {
                        value: "en_revision",
                        label: "En revisión",
                      },
                      {
                        value: "resuelto",
                        label: "Resuelto",
                      },
                      {
                        value: "cerrado",
                        label: "Cerrado",
                      },
                    ]}
                  />

                  <SelectFilter
                    label="Categoría"
                    value={ticketCategory}
                    onChange={setTicketCategory}
                    options={[
                      {
                        value: "",
                        label: "Todas las categorías",
                      },
                      {
                        value: "carcasa_rota",
                        label: "Carcasa rota",
                      },
                      {
                        value: "tapa_faltante",
                        label: "Tapa faltante",
                      },
                      {
                        value: "etiqueta_ilegible",
                        label: "Etiqueta ilegible",
                      },
                      {
                        value: "deterioro_estetico",
                        label: "Deterioro estético",
                      },
                      {
                        value: "otro",
                        label: "Otro",
                      },
                    ]}
                  />
                </div>

                {devicesError && (
                  <p
                    role="alert"
                    style={{ color: "#b91c1c" }}
                  >
                    {devicesError}
                  </p>
                )}

                <ReportMessage
                  loading={ticketsLoading}
                  error={ticketsError}
                  label="tickets"
                />

                {!ticketsLoading &&
                  !ticketsError &&
                  ticketReport && (
                    <>
                      <div style={statsStyle}>
                        <ReportStat
                          title="Total de tickets"
                          value={ticketReport.summary.total}
                        />

                        <ReportStat
                          title="Abiertos"
                          value={ticketReport.summary.abiertos}
                        />

                        <ReportStat
                          title="En revisión"
                          value={
                            ticketReport.summary.en_revision
                          }
                        />

                        <ReportStat
                          title="Resueltos"
                          value={ticketReport.summary.resueltos}
                        />

                        <ReportStat
                          title="Cerrados"
                          value={ticketReport.summary.cerrados}
                        />
                      </div>

                      {/* HU11: Gráfico histórico de tickets */}
                      <ReportTimelineChart
                        type="tickets"
                        timeline={ticketReport.timeline}
                        title="Histórico de tickets por estado"
                      />

                      <h3 style={sectionTitleStyle}>
                        Detalle de tickets
                      </h3>

                      <ReportTable
                        headings={[
                          "N.º Ticket",
                          "Dispositivo",
                          "Categoría",
                          "Descripción",
                          "Estado",
                          "Fecha de creación",
                        ]}
                        empty={
                          (ticketReport.tickets ?? []).length === 0
                        }
                        emptyMessage="No se encontraron tickets con los filtros seleccionados."
                      >
                        {(ticketReport.tickets ?? []).map((ticket) => (
                          <tr key={ticket.id}>
                            <td style={cellStyle}>
                              {ticket.ticket_number ?? "—"}
                            </td>

                            <td style={cellStyle}>
                              {ticket.device_name ||
                                ticket.device_code ||
                                "Sin dispositivo"}
                            </td>

                            <td style={cellStyle}>
                              {formatStatus(ticket.category)}
                            </td>

                            <td
                              style={{
                                ...cellStyle,
                                minWidth: "220px",
                                maxWidth: "360px",
                                overflowWrap: "anywhere",
                              }}
                            >
                              {ticket.description ||
                                "Sin descripción"}
                            </td>

                            <td style={cellStyle}>
                              {formatStatus(ticket.status)}
                            </td>

                            <td style={cellStyle}>
                              {formatDate(ticket.created_at)}
                            </td>
                          </tr>
                        ))}
                      </ReportTable>
                    </>
                  )}
              </div>
            )}

          </div>
        </div>
      </section>
    </main>
  );
}

export default ReportsPage;
