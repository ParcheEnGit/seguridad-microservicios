import React from "react";
import { Monitor } from "lucide-react";

export function DeviceTable({ devices }) {
  if (devices.length === 0) {
    return (
      <div className="reader-empty-state">
        <Monitor
          className="reader-empty-state__icon"
          size={32}
          strokeWidth={1.7}
          aria-hidden="true"
        />

        <p>No hay dispositivos disponibles.</p>

        <span>
          Cuando se registren dispositivos, podrás ver su estado aquí.
        </span>
      </div>
    );
  }

  return (
    <div className="reader-table-container">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Dispositivo</th>
            <th>Tipo</th>
            <th>Ubicación</th>
            <th>Estado</th>
            <th>Umbrales</th>
          </tr>
        </thead>

        <tbody>
          {devices.map((device) => (
            <tr key={device.id}>
              <td>
                <strong>{device.name}</strong>

                <span className="reader-device-code">
                  {device.device_code}
                </span>
              </td>

              <td>{device.device_type}</td>

              <td>{device.location}</td>

              <td>
                <span
                  className={`reader-status reader-status--${device.status}`}
                >
                  {device.status}
                </span>
              </td>

              <td>{device.thresholds?.length ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}