import React from 'react';

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: '12px' }}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton-pulse"
          style={{
            height: i === 0 ? '48px' : '36px',
            width: '100%',
            opacity: 1 - i * 0.15,
          }}
        />
      ))}
    </div>
  );
};
