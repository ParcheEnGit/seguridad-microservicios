export const ROLE_ADMIN = 0;
export const ROLE_USER = 1;

export function isAdmin(role) {
  return role === ROLE_ADMIN;
}

export function getRoleLabel(role) {
  return role === ROLE_ADMIN ? "Administrador" : "Lector";
}

export function canRegisterDevice(role) {
  return isAdmin(role);
}
