import React from 'react';
import { BackendHealth, SatelliteScene } from '../../types/satellite';

interface HeaderProps {
  selectedScene: SatelliteScene | null;
  backendHealth: BackendHealth;
  onRefreshHealth: () => void;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedScene,
  backendHealth,
  onRefreshHealth,
  onToggleMobileMenu,
}) => {
  const isConnected = backendHealth.status === 'connected';

  return (
    <header className="top-header" role="banner">
      <div className="header-left">
        {onToggleMobileMenu && (
          <button
            className="map-tool-btn"
            style={{ display: 'none' }}
            onClick={onToggleMobileMenu}
            aria-label="Toggle Navigation Menu"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
              <path d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z" />
            </svg>
          </button>
        )}

        <div className="brand-title">
          <svg className="brand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="9" />
            <path d="M3.6 9h16.8" />
            <path d="M3.6 15h16.8" />
            <path d="M11.5 3a17 17 0 0 0 0 18" />
            <path d="M12.5 3a17 17 0 0 1 0 18" />
          </svg>
          <span>SatQuery AI</span>
        </div>

        <div
          className="environment-badge"
          title={
            isConnected
              ? "Connected to local FastAPI backend with real Sentinel-2 STAC and Rasterio NDVI processing"
              : "Backend offline. Running in scientific simulation mode with mock datasets"
          }
        >
          <span className={`status-dot ${isConnected ? 'emerald' : 'cyan'}`} />
          <span>{isConnected ? 'LIVE EO BACKEND' : 'SIMULATED EO ENGINE'}</span>
        </div>
      </div>

      <div className="header-right">
        <div className="telemetry-readout">
          {selectedScene && (
            <>
              <div className="telemetry-item" title="Center Coordinates (WGS84)">
                <span className="label">AOI:</span>
                <span className="val">
                  {selectedScene.centerCoordinates.lat.toFixed(3)}°, {selectedScene.centerCoordinates.lon.toFixed(3)}°
                </span>
              </div>
              <div className="telemetry-item" title="Platform and Instrument">
                <span className="label">PLATFORM:</span>
                <span className="val">{selectedScene.platformId}</span>
              </div>
            </>
          )}

          <div
            className="telemetry-item"
            style={{ cursor: 'pointer' }}
            onClick={onRefreshHealth}
            title={`${backendHealth.message} (Click to recheck)`}
          >
            <span className={`status-dot ${isConnected ? 'emerald' : 'amber'}`} />
            <span className="label">API:</span>
            <span className="val">{isConnected ? 'ONLINE' : 'SIMULATED'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
