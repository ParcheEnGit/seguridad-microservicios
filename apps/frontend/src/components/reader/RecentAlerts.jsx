import React from "react";

export function RecentAlerts({ alerts }) {
  if (alerts.length === 0) {
    return (
      <div className="reader-empty-state">
        <p>No hay alertas recientes.</p>
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

          <p className="reader-alert__device">
            {alert.deviceName}
          </p>

          <span className="reader-alert__date">
            {alert.date}
          </span>
        </article>
      ))}
    </div>
  );
}