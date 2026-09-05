import React from 'react';

interface StatusBadgeProps {
  status: 'idle' | 'queued' | 'processing' | 'completed' | 'error' | 'pending' | 'active' | 'failed';
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, size = 'sm' }) => {
  let dotClass = 'cyan';
  let defaultLabel = status.toUpperCase();

  switch (status) {
    case 'completed':
      dotClass = 'emerald';
      defaultLabel = 'COMPLETED';
      break;
    case 'processing':
    case 'active':
      dotClass = 'cyan';
      defaultLabel = 'PROCESSING';
      break;
    case 'queued':
    case 'pending':
    case 'idle':
      dotClass = 'amber';
      defaultLabel = 'QUEUED';
      break;
    case 'error':
    case 'failed':
      dotClass = 'rose';
      defaultLabel = 'FAILED';
      break;
  }

  return (
    <span
      className="telemetry-item"
      style={{
        fontSize: size === 'sm' ? '10px' : '11px',
        padding: size === 'sm' ? '2px 6px' : '4px 8px',
      }}
    >
      <span className={`status-dot ${dotClass}`} />
      <span className="val">{label || defaultLabel}</span>
    </span>
  );
};
