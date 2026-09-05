import React from 'react';
import { BackendHealth } from '../../types/satellite';

interface SettingsViewProps {
  backendHealth: BackendHealth;
  onRefreshHealth: () => void;
  isCheckingHealth: boolean;
  onClearHistory: () => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  backendHealth,
  onRefreshHealth,
  isCheckingHealth,
  onClearHistory,
}) => {
  const isConnected = backendHealth.status === 'connected';

  return (
    <div className="view-container" aria-label="System Settings and Health Diagnostics">
      <div className="view-header">
        <div>
          <h2 className="view-title">System Telemetry & Settings</h2>
          <p className="view-subtitle">
            Diagnostics for backend API connectivity, scientific simulation parameters, and local data caches.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {/* Backend API Connection Status */}
        <section className="saved-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                FastAPI Backend Connectivity
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Target Endpoint: <code>http://localhost:8000/health</code>
              </p>
            </div>

            <button
              className="btn-analyze"
              onClick={onRefreshHealth}
              disabled={isCheckingHealth}
            >
              {isCheckingHealth ? 'Pinging...' : 'Probe API Endpoint'}
            </button>
          </div>

          <div className="meta-table" style={{ marginTop: '8px' }}>
            <div className="meta-row">
              <span className="meta-label">Connection State</span>
              <span className="meta-val">
                <span className={`status-dot ${isConnected ? 'emerald' : 'amber'}`} style={{ marginRight: '6px' }} />
                {isConnected ? 'ONLINE (Connected)' : 'STANDALONE SIMULATION (Backend Inactive)'}
              </span>
            </div>
            <div className="meta-row">
              <span className="meta-label">Reported Service Name</span>
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
        </section>

        {/* Scientific Simulation Parameters */}
        <section className="saved-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Earth Observation Simulation Mode
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            SatQuery AI is currently operating in scientific preview simulation mode. All scene
            footprints, spectral bands, atmospheric correction values, and AI analytical syntheses are
            synthesized for demonstration and evaluation purposes.
          </p>

          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '10px' }}>
            <span className="environment-badge">Sentinel-2 (MSI L2A)</span>
            <span className="environment-badge">Landsat 8/9 (OLI-2/TIRS-2)</span>
            <span className="environment-badge">Sentinel-1 (C-SAR IW)</span>
            <span className="environment-badge">PlanetScope (SuperDove 3m)</span>
          </div>
        </section>

        {/* Local Storage & Cache Controls */}
        <section className="saved-card">
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
            Cache & Browser Storage
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Manage local search audit logs and saved session states stored in your browser's localStorage.
          </p>

          <div style={{ marginTop: '10px' }}>
            <button
              className="map-tool-btn"
              style={{ width: 'auto', padding: '6px 12px', fontSize: '12px', color: 'var(--accent-rose)' }}
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
