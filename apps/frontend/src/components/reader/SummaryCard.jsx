import React from "react";

export function SummaryCard({
  title,
  value,
  description,
  icon: Icon,
  variant = "green",
}) {
  return (
    <article className="reader-summary-card">
      <div className="reader-summary-card__content">
        <span className="reader-summary-card__title">
          {title}
        </span>

        <strong className="reader-summary-card__value">
          {value}
        </strong>

        {description && (
          <span className="reader-summary-card__description">
            {description}
          </span>
        )}
      </div>

      {Icon && (
        <div
          className={`reader-summary-card__icon reader-summary-card__icon--${variant}`}
          aria-hidden="true"
        >
          <Icon size={20} strokeWidth={2} />
        </div>
      )}
    </article>
  );
}