import React from "react";

export function SummaryCard({ title, value, description }) {
  return (
    <article className="reader-summary-card">
      <span className="reader-summary-card__title">{title}</span>

      <strong className="reader-summary-card__value">
        {value}
      </strong>

      {description && (
        <span className="reader-summary-card__description">
          {description}
        </span>
      )}
    </article>
  );
}