import React from 'react';
import { SavedAnalysis } from '../../types/satellite';
import { EmptyState } from '../common/EmptyState';

interface SavedAnalysesViewProps {
  savedList: SavedAnalysis[];
  onSelectSaved: (sceneId: string) => void;
  onRemoveSaved: (id: string) => void;
}

export const SavedAnalysesView: React.FC<SavedAnalysesViewProps> = ({
  savedList,
  onSelectSaved,
  onRemoveSaved,
}) => {
  return (
    <div className="view-container" aria-label="Saved Research Analyses">
      <div className="view-header">
        <div>
          <h2 className="view-title">Saved Research Analyses</h2>
          <p className="view-subtitle">
            Bookmarked Earth observation findings, study notes, and biophysical baselines.
          </p>
        </div>
      </div>

      {savedList.length === 0 ? (
        <EmptyState
          iconType="bookmark"
          title="No Saved Analyses Yet"
          description="Click 'Bookmark Analysis' on any completed AI analysis card to save findings here."
        />
      ) : (
        <div className="saved-cards-grid">
          {savedList.map((item) => (
            <article key={item.id} className="saved-card">
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                  {item.title}
                </h3>
                <span className="mission-tag">{item.mission}</span>
              </div>

              <div style={{ fontSize: '12px', color: 'var(--accent-cyan)', fontStyle: 'italic' }}>
                "{item.query}"
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-secondary)', background: 'var(--bg-panel)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
                {item.notes}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                {item.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      background: 'rgba(255, 255, 255, 0.06)',
                      borderRadius: 'var(--radius-sm)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    #{tag}
                  </span>
                ))}
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--accent-emerald)' }}>
                  {item.keyMetric}
                </span>

                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    className="btn-analyze"
                    onClick={() => onSelectSaved(item.sceneId)}
                    title="Open this scene in the workspace"
                  >
                    Open
                  </button>
                  <button
                    className="map-tool-btn"
                    style={{ width: '26px', height: '26px' }}
                    onClick={() => onRemoveSaved(item.id)}
                    title="Remove from saved"
                  >
                    ✕
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};
