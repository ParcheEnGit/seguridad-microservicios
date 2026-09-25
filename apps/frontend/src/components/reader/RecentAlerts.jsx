import React from "react";
import { Bell } from "lucide-react";

function formatAlertDate(date) {
  if (!date) return "";

  return new Date(date).toLocaleString("es-BO", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "America/La_Paz",
  });
}

export function RecentAlerts({ alerts }) {
  if (alerts.length === 0) {
    return (
      <div className="reader-empty-state">
        <Bell
          className="reader-empty-state__icon"
          size={32}
          strokeWidth={1.7}
          aria-hidden="true"
        />

        <p>No hay alertas recientes.</p>

        <span>Las alertas activas aparecerán aquí.</span>
      </div>
    );
  }

  return (
    <div className="reader-alerts">
      {alerts.map((alert) => (
        <article key={alert.id} className="reader-alert">
          <div className="reader-alert__header">
            <strong>{alert.type}</strong>

            <span
              className={`reader-alert__severity reader-alert__severity--${alert.severity}`}
            >
              {alert.severity}
            </span>
          </div>

          <p className="reader-alert__device">{alert.deviceName}</p>

          <span className="reader-alert__date">
            {formatAlertDate(alert.date)}
          </span>
        </article>
      ))}
    </div>
  );
}
