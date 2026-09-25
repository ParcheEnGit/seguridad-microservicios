export function getUserInitials(name) {
  if (!name) {
    return "LS";
  }

  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function getRoleLabelEs(role) {
  return role === 0 ? "Administrador" : "Lector";
}

export function getRoleLabelForDisplay(role) {
  return getRoleLabelEs(role);
}
