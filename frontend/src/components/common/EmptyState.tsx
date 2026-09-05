import React from 'react';

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  iconType?: 'satellite' | 'search' | 'bookmark';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  actionLabel,
  onAction,
  iconType = 'satellite',
}) => {
  return (
    <div className="empty-state">
      {iconType === 'satellite' && (
        <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 3a9 9 0 0 0 9 9" />
          <path d="M12 3a9 9 0 0 1 9 9" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      )}

      {iconType === 'search' && (
        <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      )}

      {iconType === 'bookmark' && (
        <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
        </svg>
      )}

      <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{title}</div>
      <p style={{ fontSize: '11px', maxWidth: '280px', lineHeight: 1.4 }}>{description}</p>

      {actionLabel && onAction && (
        <button
          className="btn-analyze"
          style={{ marginTop: '8px' }}
          onClick={onAction}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
