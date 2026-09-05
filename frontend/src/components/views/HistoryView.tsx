import React from 'react';
import { QueryHistoryItem } from '../../types/satellite';
import { EmptyState } from '../common/EmptyState';

interface HistoryViewProps {
  history: QueryHistoryItem[];
  onSelectQuery: (queryText: string) => void;
  onClearHistory: () => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  history,
  onSelectQuery,
  onClearHistory,
}) => {
  return (
    <div className="view-container" aria-label="Query History Audit Trail">
      <div className="view-header">
        <div>
          <h2 className="view-title">Query History</h2>
          <p className="view-subtitle">
            Audit log of natural language questions and Earth observation catalog lookups.
          </p>
        </div>

        {history.length > 0 && (
          <button className="btn-analyze" onClick={onClearHistory}>
            Clear History
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <EmptyState
          iconType="search"
          title="No Past Queries Recorded"
          description="Your previous search queries will appear here for rapid re-execution."
        />
      ) : (
        <table className="data-table" aria-label="Query History Table">
          <thead>
            <tr>
              <th>Timestamp (UTC)</th>
              <th>Natural Language Query</th>
              <th>Target Location / AOI</th>
              <th>Mission Filter</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item) => (
              <tr key={item.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', whiteSpace: 'nowrap' }}>
                  {new Date(item.timestamp).toLocaleString()}
                </td>
                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.query}</td>
                <td>{item.locationName}</td>
                <td>
                  <span className="environment-badge" style={{ fontSize: '10px' }}>
                    {item.missionFilter || 'All'}
                  </span>
                </td>
                <td>
                  <button
                    className="btn-analyze"
                    onClick={() => onSelectQuery(item.query)}
                    title="Re-run this query in workspace"
                  >
                    Re-run
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};
