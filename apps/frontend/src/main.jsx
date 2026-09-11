import React from "react";
import { createRoot } from "react-dom/client";
import { Activity, ShieldCheck } from "lucide-react";
import "./styles.css";

function App() {
  return (
    <main className="landing">
      <section className="card" aria-labelledby="app-title">
        <div className="brand">
          <Activity aria-hidden="true" />
          <span>LabWatch</span>
        </div>
        <h1 id="app-title">Monitoreo seguro de laboratorios</h1>
        <p>
          La base del frontend está lista. El siguiente paso es integrar
          Keycloak y las vistas de Admin y Lector.
        </p>
        <div className="status">
          <ShieldCheck aria-hidden="true" /> Entorno inicial configurado
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
