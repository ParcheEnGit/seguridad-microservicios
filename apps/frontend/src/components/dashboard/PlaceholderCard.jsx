import React from "react";

export function PlaceholderCard({ title }) {
  return (
    <article className="dashboard-card dashboard-card--placeholder">
      {title && <h2 className="dashboard-card__title">{title}</h2>}
      <p className="dashboard-card__placeholder-text">agregar datos</p>
    </article>
  );
}
