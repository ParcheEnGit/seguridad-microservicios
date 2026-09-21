import React from "react";
import { getUserInitials } from "../../utils/userDisplay.js";

export function UserAvatar({ user, className = "" }) {
  if (user.picture_url) {
    return (
      <img
        className={`dashboard-user-chip__avatar dashboard-user-chip__avatar--image ${className}`.trim()}
        src={user.picture_url}
        alt={`${user.name} profile`}
        referrerPolicy="no-referrer"
      />
    );
  }

  return (
    <div
      className={`dashboard-user-chip__avatar ${className}`.trim()}
      aria-hidden="true"
    >
      {getUserInitials(user.name)}
    </div>
  );
}
