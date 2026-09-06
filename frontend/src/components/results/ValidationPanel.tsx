import React, { useEffect, useState } from 'react';
import { SatelliteScene, InputValidationResponse } from '../../types/satellite';
import { apiClient } from '../../services/apiClient';

interface ValidationPanelProps {
  scene: SatelliteScene | null;
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ scene }) => {
  const [validationReport, setValidationReport] = useState<InputValidationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scene) {
      setValidationReport(null);
      setError(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    apiClient
      .validateScene(scene.id)
      .then((report: InputValidationResponse) => {
        if (isMounted) {
          setValidationReport(report);
          setIsLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'Validation request failed');
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [scene?.id]);

  if (!scene) {
    return (
      <div className="panel-content">
        <div className="empty-state">
          <p>Select a satellite scene from the catalog to run input and geospatial validation.</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="panel-content">
        <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--text-secondary)' }}>
          <div className="status-dot cyan pulse" style={{ width: '12px', height: '12px', margin: '0 auto 12px' }} />
          <div style={{ fontSize: '12px', fontWeight: 600 }}>Executing Geospatial & Input Validation...</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', fontFamily: 'var(--font-mono)' }}>
            Inspecting STAC assets & raster profiles for {scene.id}
          </div>
        </div>
      </div>
    );
  }

  if (error || !validationReport) {
    return (
      <div className="panel-content">
        <div
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(244, 63, 94, 0.1)',
            border: '1px solid var(--accent-rose)',
            color: 'var(--text-primary)',
            fontSize: '12px',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--accent-rose)', marginBottom: '4px' }}>
            Validation Failed to Load
          </div>
          <p style={{ margin: 0, color: 'var(--text-secondary)' }}>{error || 'No validation report generated.'}</p>
          <button
            className="btn btn-secondary btn-sm"
            style={{ marginTop: '12px' }}
            onClick={() => {
              if (scene) {
                setIsLoading(true);
                setError(null);
                apiClient
                  .validateScene(scene.id)
                  .then((r: InputValidationResponse) => setValidationReport(r))
                  .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)))
                  .finally(() => setIsLoading(false));
              }
            }}
          >
            Retry Validation
          </button>
        </div>
      </div>
    );
  }

  const { overall_status, modality, ndvi_ready, metadata, quality, checks, warnings, limitations } =
    validationReport;

  const getStatusBadge = (status: 'passed' | 'warning' | 'failed') => {
    switch (status) {
      case 'passed':
        return {
          bg: 'rgba(0, 214, 143, 0.15)',
          color: 'var(--accent-emerald)',
          border: 'rgba(0, 214, 143, 0.4)',
          text: '✓ PASSED',
        };
      case 'warning':
        return {
          bg: 'rgba(245, 158, 11, 0.15)',
          color: 'var(--accent-amber)',
          border: 'rgba(245, 158, 11, 0.4)',
          text: '⚠ WARNING',
        };
      case 'failed':
      default:
        return {
          bg: 'rgba(244, 63, 94, 0.15)',
          color: 'var(--accent-rose)',
          border: 'rgba(244, 63, 94, 0.4)',
          text: '✕ FAILED',
        };
    }
  };

  const overallBadge = getStatusBadge(overall_status);

  return (
    <div className="panel-content" aria-label="Input and Geospatial Validation Results">
      {/* Top Status Card */}
      <div
        style={{
          padding: '12px 14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-card)',
          border: `1px solid ${overallBadge.border}`,
          marginBottom: '12px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              background: overallBadge.bg,
              color: overallBadge.color,
              fontWeight: 700,
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              border: `1px solid ${overallBadge.border}`,
            }}
          >
            {overallBadge.text}
          </span>
          <span
            style={{
              padding: '2px 8px',
              borderRadius: 'var(--radius-sm)',
              background: ndvi_ready ? 'rgba(56, 189, 248, 0.15)' : 'rgba(100, 116, 139, 0.2)',
              color: ndvi_ready ? 'var(--accent-cyan)' : 'var(--text-muted)',
              fontSize: '11px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 600,
            }}
          >
            {ndvi_ready ? 'NDVI Ready' : 'NDVI Incompatible'}
          </span>
        </div>

        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
          Modality: {modality.toUpperCase()}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>
          Scene: {scene.id}
        </div>
      </div>

      {/* Extracted Geospatial Metadata Table */}
      <div className="panel-title" style={{ marginBottom: '6px' }}>
        <span>Extracted Geospatial Metadata</span>
      </div>
      <div className="meta-table" style={{ marginBottom: '16px' }}>
        <div className="meta-row">
          <span className="meta-label">CRS / Projection</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)' }}>
            {metadata.crs || (metadata.epsg ? `EPSG:${metadata.epsg}` : 'Unreferenced')}
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Geographic Bounds</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)', fontSize: '10px' }}>
            {metadata.bounds
              ? `[${metadata.bounds.map((v) => v.toFixed(2)).join(', ')}]`
              : 'None'}
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Raster Dimensions</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)' }}>
            {metadata.dimensions ? `${metadata.dimensions.width} × ${metadata.dimensions.height} px` : 'Header declared'}
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Spatial Resolution</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)' }}>
            {metadata.spatial_resolution_meters ? `${metadata.spatial_resolution_meters}m GSD` : 'N/A'}
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Band Count / Format</span>
          <span className="meta-val">
            {metadata.band_count || scene.bands.length} assets ({metadata.declared_format || 'COG'})
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">NoData Declaration</span>
          <span className="meta-val" style={{ fontFamily: 'var(--font-mono)' }}>
            {metadata.nodata_value !== null && metadata.nodata_value !== undefined ? String(metadata.nodata_value) : '0 (Reflectance Mask)'}
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Atmospheric / Cloud</span>
          <span className="meta-val">
            {quality.cloud_cover_percent !== null && quality.cloud_cover_percent !== undefined
              ? `${quality.cloud_cover_percent.toFixed(1)}% (${quality.quality_assessment})`
              : 'Unverified'}
          </span>
        </div>
      </div>

      {/* Validation Checklist Breakdown */}
      <div className="panel-title" style={{ marginBottom: '8px' }}>
        <span>Validation Checks ({checks.length})</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {checks.map((check) => {
          const badge = getStatusBadge(check.status);
          return (
            <div
              key={check.id}
              style={{
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                fontSize: '11px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{check.label}</span>
                <span
                  style={{
                    padding: '1px 6px',
                    borderRadius: '2px',
                    background: badge.bg,
                    color: badge.color,
                    fontSize: '9px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                  }}
                >
                  {badge.text}
                </span>
              </div>
              <div style={{ color: 'var(--text-secondary)', lineHeight: '1.4' }}>{check.message}</div>
            </div>
          );
        })}
      </div>

      {/* Warnings & Limitations Callouts */}
      {warnings.length > 0 && (
        <div
          style={{
            padding: '10px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(245, 158, 11, 0.08)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            marginBottom: '12px',
            fontSize: '11px',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '4px' }}>
            Validation Warnings ({warnings.length})
          </div>
          <ul style={{ margin: 0, paddingLeft: '16px', color: 'var(--text-secondary)' }}>
            {warnings.map((w, idx) => (
              <li key={idx} style={{ marginBottom: '2px' }}>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {limitations.length > 0 && (
        <div
          style={{
            padding: '10px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            fontSize: '10px',
            color: 'var(--text-muted)',
          }}
        >
          <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '4px' }}>
            Phase 2 Validation Boundaries
          </div>
          <ul style={{ margin: 0, paddingLeft: '16px' }}>
            {limitations.map((lim, idx) => (
              <li key={idx} style={{ marginBottom: '2px' }}>
                {lim}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
