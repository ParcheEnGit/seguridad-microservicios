import {
  Bell,
  FileText,
  Home,
  Radio,
  Settings,
  Ticket,
  Users,
  Wifi,
} from "lucide-react";
import { ROLE_ADMIN, ROLE_USER } from "./roles.js";

export const NAV_ITEMS = [
  { id: "inicio", label: "Inicio", icon: Home, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "dispositivos", label: "Dispositivos", icon: Wifi, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "telemetria", label: "Telemetría", icon: Radio, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "alertas", label: "Alertas", icon: Bell, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "tickets", label: "Tickets", icon: Ticket, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "reportes", label: "Reportes", icon: FileText, roles: [ROLE_ADMIN] },
  { id: "usuarios", label: "Usuarios", icon: Users, roles: [ROLE_ADMIN] },
  { id: "configuracion", label: "Configuración", icon: Settings, roles: [ROLE_ADMIN] },
];

export function getNavItemsForRole(role) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}
