import React, { useState } from 'react';
import { AnalysisResult, SatelliteScene } from '../../types/satellite';

interface ResultSummaryCardProps {
  result: AnalysisResult | null;
  scene: SatelliteScene | null;
  onSaveAnalysis: (result: AnalysisResult, scene: SatelliteScene, notes: string) => void;
  isSaved: boolean;
}

export const ResultSummaryCard: React.FC<ResultSummaryCardProps> = ({
  result,
  scene,
  onSaveAnalysis,
  isSaved,
}) => {
  const [showNotesInput, setShowNotesInput] = useState(false);
  const [userNotes, setUserNotes] = useState('');
  const [exportNotice, setExportNotice] = useState<string | null>(null);

  if (!result || !scene) {
    return null;
  }

  const handleExport = (format: string) => {
    setExportNotice(
      `Demo Export (${format}): Mock dataset prepared. File download is unavailable until backend export pipeline integration.`
    );
    setTimeout(() => setExportNotice(null), 4000);
  };

  const handleSave = () => {
    onSaveAnalysis(result, scene, userNotes);
    setShowNotesInput(false);
  };

  return (
    <article className="result-card" aria-label="Simulated AI Analysis Synthesis">
      <div className="result-card-header">
        <div>
          <span className="panel-title" style={{ fontSize: '11px' }}>
            {result.isRealAnalysis ? 'Real Sentinel-2 L2A NDVI Analysis' : 'Simulated AI Analysis Synthesis'}
          </span>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            Analyzed {result.areaAnalyzedSqKm} km² footprint {result.isRealAnalysis ? '(Rasterio Bounded Read @ 10m)' : ''}
          </div>
        </div>

        {result.confidenceScorePercent !== null ? (
          <div className="confidence-gauge" title="Simulated statistical confidence score (Demonstration metric)">
            CONFIDENCE: {result.confidenceScorePercent.toFixed(1)}% (SIMULATED)
          </div>
        ) : (
          <div
            className="telemetry-item"
            style={{ fontSize: '10px', color: 'var(--text-muted)' }}
            title="Scientific notice: Single observation provides biophysical reflectance only. Statistical confidence interval is not applicable."
          >
            CONFIDENCE: N/A (SINGLE PASS)
          </div>
        )}
      </div>

      {/* Executive Summary */}
      <div className="result-summary-text">
        <p>{result.executiveSummary}</p>
      </div>

      {/* Key Findings List */}
      <div>
        <span className="chip-label" style={{ marginBottom: '6px', display: 'block' }}>
          {result.isRealAnalysis ? 'Computed Biophysical Findings:' : 'Key Analytical Findings (Demo):'}
        </span>
        <ul className="findings-list">
          {result.keyFindings.map((finding, idx) => (
            <li key={idx}>{finding}</li>
          ))}
        </ul>
      </div>

      {/* Metric Deltas Grid */}
      <div>
        <span className="chip-label" style={{ marginBottom: '6px', display: 'block' }}>
          {result.isRealAnalysis ? 'Measured Biophysical Indicators:' : 'Estimated Biophysical Indicators:'}
        </span>
        <div className="metrics-grid">
          {result.metricDeltas.map((metric, idx) => (
            <div key={idx} className="metric-box">
              <span className="metric-label">{metric.label}</span>
              <div className="metric-val-row">
                <span className="metric-value">{metric.value}</span>
                {metric.change && (
                  <span className={`metric-delta ${metric.trend}`}>
                    {metric.change}
                  </span>
                )}
              </div>
              <span style={{ fontSize: '9px', color: 'var(--text-muted)' }}>
                Baseline: {metric.baseline}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Anomalies Box */}
      {typeof result.anomaliesDetectedCount === 'number' && result.anomaliesDetectedCount > 0 && (
        <div
          style={{
            background: 'rgba(244, 63, 94, 0.08)',
            border: '1px solid rgba(244, 63, 94, 0.25)',
            borderRadius: 'var(--radius-sm)',
            padding: '8px 10px',
            fontSize: '11px',
            color: 'var(--text-primary)',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--accent-rose)', marginBottom: '3px' }}>
            ⚠️ {result.anomaliesDetectedCount} Spatial Anomaly Candidate(s) Flagged
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>
            {result.anomalyNotes}
          </p>
        </div>
      )}

      {/* Methodology & Citation */}
      <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
        <div>Methodology: {result.methodologyCitation}</div>
      </div>

      {/* Scientific Demonstration Disclaimer */}
      <div className="demo-disclaimer">
        {result.disclaimer}
      </div>

      {/* Export & Save Action Bar */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {exportNotice && (
          <div
            style={{
              padding: '6px 8px',
              background: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11px',
              color: 'var(--accent-cyan)',
            }}
          >
            {exportNotice}
          </div>
        )}

        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          <button
            className="btn-analyze"
            onClick={() => handleExport('GeoJSON')}
            title="Export simulated vector boundaries (Demo)"
          >
            Export GeoJSON (Demo)
          </button>
          <button
            className="btn-analyze"
            onClick={() => handleExport('STAC Item')}
            title="Export STAC JSON Metadata (Demo)"
          >
            Export STAC (Demo)
          </button>
          <button
            className="btn-analyze"
            onClick={() => setShowNotesInput(!showNotesInput)}
            style={{ marginLeft: 'auto' }}
          >
            {isSaved ? '✓ Saved to Bookmarks' : 'Bookmark Analysis'}
          </button>
        </div>

        {showNotesInput && !isSaved && (
          <div style={{ display: 'flex', gap: '6px', marginTop: '6px' }}>
            <input
              type="text"
              className="query-input"
              style={{ fontSize: '11px', padding: '6px 8px' }}
              placeholder="Add scientific study notes..."
              value={userNotes}
              onChange={(e) => setUserNotes(e.target.value)}
            />
            <button className="btn-analyze" onClick={handleSave}>
              Save
            </button>
          </div>
        )}
      </div>
    </article>
  );
};
