import React from "react";

export function DeviceTable({ devices }) {
  if (devices.length === 0) {
    return (
      <div className="reader-empty-state">
        <p>No hay dispositivos disponibles.</p>
      </div>
    );
  }

  return (
    <div className="reader-table-container">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Dispositivo</th>
            <th>Laboratorio</th>
            <th>Estado</th>
            <th>Temperatura</th>
            <th>Humedad</th>
          </tr>
        </thead>

        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>{device.name}</td>
              <td>{device.laboratory}</td>
              <td>
                <span
                  className={`reader-status reader-status--${device.status}`}
                >
                  {device.status === "active" ? "Activo" : "Inactivo"}
                </span>
              </td>
              <td>
                {device.temperature != null
                  ? `${device.temperature} °C`
                  : "Sin datos"}
              </td>
              <td>
                {device.humidity != null
                  ? `${device.humidity} %`
                  : "Sin datos"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}