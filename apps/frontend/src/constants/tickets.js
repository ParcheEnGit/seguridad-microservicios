export const TICKET_CATEGORIES = [
  { value: "carcasa_rota", label: "Carcasa dañada" },
  { value: "tapa_faltante", label: "Tapa faltante" },
  { value: "etiqueta_ilegible", label: "Etiqueta ilegible" },
  { value: "cable_deteriorado", label: "Cable deteriorado" },
  { value: "conector_suelto", label: "Conector suelto" },
  { value: "pantalla_danada", label: "Pantalla dañada" },
  { value: "suciedad_acumulada", label: "Suciedad acumulada" },
  { value: "deterioro_estetico", label: "Deterioro estético" },
  { value: "otro", label: "Otro" },
];

export const TICKET_STATUSES = [
  { value: "abierto", label: "Abierto" },
  { value: "en_revision", label: "En revisión" },
  { value: "resuelto", label: "Resuelto" },
  { value: "cerrado", label: "Cerrado" },
];

export const TICKET_DESCRIPTION_MIN = 10;
export const TICKET_DESCRIPTION_MAX = 2000;
export const TICKET_ATTACHMENT_TYPES = ["application/pdf", "image/png", "image/jpeg"];
export const TICKET_ATTACHMENT_MAX_BYTES = 5 * 1024 * 1024;

export function getCategoryLabel(value) {
  return TICKET_CATEGORIES.find((category) => category.value === value)?.label ?? value;
}

export function getStatusLabel(value) {
  return TICKET_STATUSES.find((status) => status.value === value)?.label ?? value;
}
