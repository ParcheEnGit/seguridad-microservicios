// Compose expone el mismo valor usado por simulator-device. Se aplica el mismo
// mínimo del simulador para que las gráficas no consulten más rápido de lo que
// se generan lecturas nuevas.
const configuredSeconds = Number.parseInt(import.meta.env.VITE_SIMULATOR_INTERVAL_SECONDS ?? "15", 10);

export const TELEMETRY_REFRESH_SECONDS = Math.max(5, Number.isFinite(configuredSeconds) ? configuredSeconds : 15);
export const TELEMETRY_REFRESH_MS = TELEMETRY_REFRESH_SECONDS * 1000;
