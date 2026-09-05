import React from 'react';
import { AnalysisJob } from '../../types/satellite';

interface AnalysisStatusPanelProps {
  job: AnalysisJob | null;
}

export const AnalysisStatusPanel: React.FC<AnalysisStatusPanelProps> = ({ job }) => {
  if (!job) {
    return (
      <div className="analysis-panel">
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', textAlign: 'center', padding: '16px' }}>
          No active pipeline job. Click <strong>"Run AI Analysis"</strong> on any scene to initiate simulated Earth observation inference.
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-panel" aria-label="Analysis Pipeline Telemetry">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="panel-title" style={{ fontSize: '11px' }}>
          Simulated Pipeline Telemetry
        </span>
        <span className="environment-badge" style={{ fontSize: '10px' }}>
          {job.status.toUpperCase()} ({job.progressPercent}%)
        </span>
      </div>

      {/* Progress Bar */}
      <div className="pipeline-progress-bar" role="progressbar" aria-valuenow={job.progressPercent} aria-valuemin={0} aria-valuemax={100}>
        <div
          className="pipeline-progress-fill"
          style={{ width: `${job.progressPercent}%` }}
        />
      </div>

      {/* Stages List */}
      <div className="stages-list">
        {job.stages.map((stage, idx) => {
          let statusIcon = '⏳';
          let textColor = 'var(--text-muted)';

          if (stage.status === 'completed') {
            statusIcon = '✓';
            textColor = 'var(--accent-emerald)';
          } else if (stage.status === 'active') {
            statusIcon = '▶';
            textColor = 'var(--accent-cyan)';
          }

          return (
            <div key={stage.id} className="stage-row">
              <span className="stage-status-icon" style={{ color: textColor, fontWeight: 700 }}>
                {statusIcon}
              </span>
              <div className="stage-content">
                <div className="stage-title" style={{ color: textColor }}>
                  {idx + 1}. {stage.name}
                  {stage.elapsedMs && (
                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginLeft: '6px' }}>
                      ({stage.elapsedMs}ms)
                    </span>
                  )}
                </div>
                <div className="stage-detail">{stage.detail}</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Terminal Log Stream */}
      <div className="terminal-log" aria-label="Telemetry Logs">
        <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>
          [EO-ENGINE-STREAM] Job {job.jobId}
        </div>
        {job.stages
          .filter((s) => s.logMessage)
          .map((s) => (
            <div key={s.id} style={{ marginBottom: '2px' }}>
              &gt; {s.logMessage}
            </div>
          ))}
        {job.status === 'processing' && <div>&gt; Awaiting stage callback...</div>}
        {job.status === 'completed' && (
          <div style={{ color: 'var(--accent-emerald)' }}>
            &gt; Pipeline complete. Synthesis ready.
          </div>
        )}
      </div>
    </div>
  );
};
