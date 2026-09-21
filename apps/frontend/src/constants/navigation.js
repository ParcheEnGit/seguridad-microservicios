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
  { id: "home", label: "Home", icon: Home, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "devices", label: "Devices", icon: Wifi, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "telemetry", label: "Telemetry", icon: Radio, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "alerts", label: "Alerts", icon: Bell, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "tickets", label: "Tickets", icon: Ticket, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "reports", label: "Reports", icon: FileText, roles: [ROLE_ADMIN, ROLE_USER] },
  { id: "users", label: "Users", icon: Users, roles: [ROLE_ADMIN] },
  { id: "settings", label: "Settings", icon: Settings, roles: [ROLE_ADMIN] },
];

export function getNavItemsForRole(role) {
  return NAV_ITEMS.filter((item) => item.roles.includes(role));
}
