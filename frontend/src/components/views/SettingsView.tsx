import React from 'react';
import { BackendHealth } from '../../types/satellite';
import { BACKEND_BASE_URL } from '../../services/apiClient';

interface SettingsViewProps {
  backendHealth: BackendHealth;
  onRefreshHealth: () => void;
  isCheckingHealth: boolean;
  onClearHistory: () => void;
  operationalMode: 'live' | 'simulated';
  onSetOperationalMode: (mode: 'live' | 'simulated') => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  backendHealth,
  onRefreshHealth,
  isCheckingHealth,
  onClearHistory,
  operationalMode,
  onSetOperationalMode,
}) => {
  const isConnected = backendHealth.status === 'connected';
  const isLive = operationalMode === 'live';

  return (
    <div className="view-container" aria-label="System Settings and Health Diagnostics">
      <div className="view-header">
        <div>
          <h2 className="view-title">System Telemetry & Settings</h2>
          <p className="view-subtitle">
            Diagnostics for backend API connectivity, operational modes, and deployment configuration.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Operational Mode Toggle */}
        <section className="saved-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
            Operational Engine Mode
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: 1.5 }}>
            Select whether SatQuery AI should interact directly with your live FastAPI backend (with public AWS Sentinel-2 STAC and Rasterio NDVI computation) or operate in standalone simulation mode with curated benchmark scenes.
          </p>

          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
              <input
                type="radio"
                name="operationalMode"
                value="live"
                checked={isLive}
                onChange={() => onSetOperationalMode('live')}
              />
              <span style={{ fontWeight: 600, color: isLive ? 'var(--accent-emerald)' : 'var(--text-primary)' }}>
                Live Backend Mode (STAC & Rasterio)
              </span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }}>
              <input
                type="radio"
                name="operationalMode"
                value="simulated"
                checked={!isLive}
                onChange={() => onSetOperationalMode('simulated')}
              />
              <span style={{ fontWeight: 600, color: !isLive ? 'var(--accent-cyan)' : 'var(--text-primary)' }}>
                Simulated Mode (Offline Benchmark Data)
              </span>
            </label>
          </div>

          <div style={{ marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
            {isLive
              ? '⚡ Live Mode Active: All search and analysis queries target the live backend. If the backend is unreachable, clear error notifications will be displayed.'
              : '🧪 Simulated Mode Active: Queries return curated benchmark scenes with simulated pipelines without calling external servers.'}
          </div>
        </section>

        {/* Backend API Connection Status */}
        <section className="saved-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                FastAPI Backend Connectivity
              </h3>
            </div>

            <button
              className="btn-analyze"
              onClick={onRefreshHealth}
              disabled={isCheckingHealth}
            >
              {isCheckingHealth ? 'Pinging...' : 'Probe API Endpoint'}
            </button>
          </div>

          <div className="meta-table" style={{ marginTop: '12px' }}>
            <div className="meta-row">
              <span className="meta-label">Connection State</span>
              <span className="meta-val">
                <span className={`status-dot ${isConnected ? 'emerald' : isLive ? 'rose' : 'cyan'}`} style={{ marginRight: '6px' }} />
                {isConnected
                  ? 'ONLINE (Connected)'
                  : isLive
                  ? 'OFFLINE (FastAPI Unreachable)'
                  : 'STANDALONE (Simulated Mode)'}
              </span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Configured API Base URL</span>
              <span className="meta-val"><code>{BACKEND_BASE_URL}</code></span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Reported Service</span>
              <span className="meta-val">{backendHealth.service}</span>
            </div>
            {backendHealth.latencyMs !== undefined && (
              <div className="meta-row">
                <span className="meta-label">Round-Trip Latency</span>
                <span className="meta-val">{backendHealth.latencyMs} ms</span>
              </div>
            )}
            <div className="meta-row">
              <span className="meta-label">Last Heartbeat Probe</span>
              <span className="meta-val">{new Date(backendHealth.lastChecked).toLocaleTimeString()}</span>
            </div>
          </div>

          {/* Public Deployment Guidance Callout */}
          <div
            style={{
              marginTop: '16px',
              padding: '12px 14px',
              background: 'rgba(2, 132, 199, 0.08)',
              border: '1px solid rgba(2, 132, 199, 0.25)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '11.5px',
              lineHeight: 1.5,
              color: 'var(--text-secondary)',
            }}
          >
            <strong style={{ color: 'var(--accent-cyan)' }}>ℹ️ Public Deployment Notice (Netlify / Vercel):</strong>
            <p style={{ marginTop: '4px' }}>
              The fallback URL <code>http://localhost:8000</code> works <strong>only for local development</strong> on your own machine.
              On a publicly hosted frontend (such as Netlify), web browsers cannot contact <code>localhost:8000</code> because it refers to the client device's loopback interface.
            </p>
            <p style={{ marginTop: '4px' }}>
              To enable live remote sensing capabilities in production, deploy the FastAPI backend to a cloud host (Render, Railway, Fly.io, or AWS EC2) and configure the public HTTPS URL in Netlify as:
              <br />
              <code style={{ display: 'inline-block', marginTop: '4px', background: 'var(--bg-secondary)', padding: '2px 6px', borderRadius: '4px' }}>
                NEXT_PUBLIC_API_BASE_URL=https://your-backend-api.domain.com
              </code>
            </p>
          </div>
        </section>

        {/* Local Storage & Cache Controls */}
        <section className="saved-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Cache & Browser Storage
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Query history and saved bookmarks are stored locally in your browser (LocalStorage).
          </p>
          <div style={{ marginTop: '12px' }}>
            <button
              onClick={() => {
                if (window.confirm('Clear all stored query history?')) {
                  onClearHistory();
                  alert('Query history cleared.');
                }
              }}
            >
              Clear Query History Cache
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};
