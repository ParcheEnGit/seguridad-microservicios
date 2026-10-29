import React, { useEffect, useId, useRef, useState } from "react";
import { AlertTriangle, Bell, Menu, Monitor, Search, X } from "lucide-react";
import logoUrl from "../../assets/labsentinel-mark.svg";
import { fetchAlerts } from "../../services/dashboardApi.js";
import { listDevices } from "../../services/deviceApi.js";

const SEVERITY_LABELS = {
  critica: "Crítica",
  advertencia: "Advertencia",
};

function matchesAlert(alert, term) {
  const haystack = [
    alert.deviceName,
    alert.device_name,
    alert.type,
    alert.metric_code,
    alert.severity,
    SEVERITY_LABELS[alert.severity],
    alert.status,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  return haystack.includes(term);
}

export function Topbar({
  isMobileMenuOpen,
  onToggleMobileMenu,
  onOpenNotifications,
  onNavigateToDeviceSearch,
  onNavigateToAlert,
}) {
  const inputId = useId();
  const rootRef = useRef(null);
  const [notificationCount, setNotificationCount] = useState(0);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    let mounted = true;
    const loadNotifications = async () => {
      try {
        const alertsData = await fetchAlerts();
        if (mounted) {
          setNotificationCount(
            Array.isArray(alertsData) ? alertsData.length : alertsData.items?.length ?? 0,
          );
        }
      } catch {
        if (mounted) setNotificationCount(0);
      }
    };
    loadNotifications();
    const timer = setInterval(loadNotifications, 15_000);
    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const term = query.trim();
    if (term.length < 1) {
      setDevices([]);
      setAlerts([]);
      setLoading(false);
      return undefined;
    }

    let mounted = true;
    setLoading(true);
    const timer = setTimeout(async () => {
      try {
        const [deviceResult, alertResult] = await Promise.allSettled([
          listDevices({ search: term, limit: 5 }),
          fetchAlerts(),
        ]);

        if (!mounted) return;

        setDevices(
          deviceResult.status === "fulfilled" ? deviceResult.value.items ?? [] : [],
        );

        if (alertResult.status === "fulfilled") {
          const allAlerts = Array.isArray(alertResult.value)
            ? alertResult.value
            : alertResult.value.items ?? [];
          const normalized = term.toLowerCase();
          setAlerts(allAlerts.filter((alert) => matchesAlert(alert, normalized)).slice(0, 5));
        } else {
          setAlerts([]);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }, 250);

    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [query]);

  useEffect(() => {
    function handlePointerDown(event) {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    }
    function handleKeyDown(event) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  function selectDevice(device) {
    setQuery(device.name);
    setOpen(false);
    onNavigateToDeviceSearch?.(device.name);
  }

  function selectAlert(alert) {
    setQuery(alert.deviceName || alert.device_name || alert.type || "");
    setOpen(false);
    onNavigateToAlert?.(alert.id);
  }

  function submitSearch(event) {
    event.preventDefault();
    const term = query.trim();
    if (!term) return;
    setOpen(false);
    if (devices.length > 0 || alerts.length === 0) {
      onNavigateToDeviceSearch?.(term);
      return;
    }
    onNavigateToAlert?.(alerts[0].id);
  }

  const showPanel = open && query.trim().length > 0;
  const hasResults = devices.length > 0 || alerts.length > 0;

  return (
    <header className="dashboard-topbar">
      <button
        type="button"
        className="dashboard-menu-btn"
        onClick={onToggleMobileMenu}
        aria-label={isMobileMenuOpen ? "Cerrar menú" : "Abrir menú"}
        aria-expanded={isMobileMenuOpen}
      >
        {isMobileMenuOpen ? <X size={21} /> : <Menu size={21} />}
      </button>
      <div className="dashboard-mobile-brand" aria-hidden="true">
        <img src={logoUrl} alt="" />
        <strong>LabSentinel</strong>
      </div>

      <div className="dashboard-search-wrap" ref={rootRef}>
        <form className="dashboard-search" role="search" onSubmit={submitSearch}>
          <Search size={18} aria-hidden="true" />
          <input
            id={inputId}
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            placeholder="Buscar dispositivo o alerta..."
            autoComplete="off"
            aria-autocomplete="list"
            aria-expanded={showPanel}
            aria-controls={`${inputId}-results`}
          />
        </form>

        {showPanel && (
          <div
            id={`${inputId}-results`}
            className="dashboard-search-results"
            role="listbox"
            aria-label="Resultados de búsqueda"
          >
            {loading && <p className="dashboard-search-results__status">Buscando...</p>}
            {!loading && !hasResults && (
              <p className="dashboard-search-results__status">
                Sin coincidencias para “{query.trim()}”.
              </p>
            )}
            {!loading && devices.length > 0 && (
              <section>
                <h2>Dispositivos</h2>
                <ul>
                  {devices.map((device) => (
                    <li key={device.id}>
                      <button type="button" role="option" onClick={() => selectDevice(device)}>
                        <Monitor size={16} aria-hidden="true" />
                        <span>
                          <strong>{device.name}</strong>
                          <small>
                            {device.device_code} · {device.location}
                          </small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )}
            {!loading && alerts.length > 0 && (
              <section>
                <h2>Alertas</h2>
                <ul>
                  {alerts.map((alert) => (
                    <li key={alert.id}>
                      <button type="button" role="option" onClick={() => selectAlert(alert)}>
                        <AlertTriangle size={16} aria-hidden="true" />
                        <span>
                          <strong>
                            {alert.deviceName || alert.device_name || "Dispositivo"}
                          </strong>
                          <small>
                            {alert.type || alert.metric_code || "Alerta"}
                            {alert.severity
                              ? ` · ${SEVERITY_LABELS[alert.severity] ?? alert.severity}`
                              : ""}
                          </small>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        )}
      </div>

      <div className="dashboard-topbar__actions">
        <div className="dashboard-status">
          <span className="dashboard-status__dot" aria-hidden="true" />
          Conectado
        </div>

        <button
          type="button"
          className="dashboard-icon-btn"
          aria-label={`Notificaciones${notificationCount ? `: ${notificationCount} activas` : ""}`}
          onClick={onOpenNotifications}
        >
          <Bell size={18} />
          {notificationCount > 0 && (
            <span className="dashboard-icon-btn__badge">
              {notificationCount > 99 ? "99+" : notificationCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
