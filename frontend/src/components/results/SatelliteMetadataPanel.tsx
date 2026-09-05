import React from 'react';
import { SatelliteScene } from '../../types/satellite';

interface SatelliteMetadataPanelProps {
  scene: SatelliteScene | null;
}

export const SatelliteMetadataPanel: React.FC<SatelliteMetadataPanelProps> = ({ scene }) => {
  if (!scene) {
    return (
      <div className="panel-content">
        <div className="empty-state">
          <p>Select a satellite scene from the catalog to inspect STAC metadata and spectral bands.</p>
        </div>
      </div>
    );
  }

  const [minLon, minLat, maxLon, maxLat] = scene.boundingBox;

  return (
    <div className="panel-content" aria-label="Satellite STAC Metadata & Bands">
      {/* Scene Overview Header */}
      <div>
        <div style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
          {scene.title}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          ID: {scene.id}
        </div>
      </div>

      {/* STAC Metadata Key-Value Table */}
      <div className="meta-table">
        <div className="meta-row">
          <span className="meta-label">Mission Platform</span>
          <span className="meta-val">{scene.platformId}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Instrument</span>
          <span className="meta-val">{scene.instrument}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Acquisition UTC</span>
          <span className="meta-val">{new Date(scene.acquisitionDate).toUTCString()}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Processing Level</span>
          <span className="meta-val">{scene.processingLevel}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Coordinate Reference</span>
          <span className="meta-val">{scene.crs}</span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Sun Elevation / Azimuth</span>
          <span className="meta-val">
            {scene.sunElevationDeg}° / {scene.sunAzimuthDeg}°
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Bounding Box (WGS84)</span>
          <span className="meta-val">
            [{minLon.toFixed(2)}, {minLat.toFixed(2)}, {maxLon.toFixed(2)}, {maxLat.toFixed(2)}]
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Orbit Track / Path</span>
          <span className="meta-val">
            {scene.orbitPass} (Rel: {scene.relativeOrbitNumber})
          </span>
        </div>
        <div className="meta-row">
          <span className="meta-label">Granule Asset Size</span>
          <span className="meta-val">{scene.dataSizeMb.toFixed(1)} MB</span>
        </div>
      </div>

      {/* Spectral Bands Visualizer */}
      <div className="bands-visualizer">
        <div className="panel-title" style={{ marginBottom: '6px' }}>
          <span>Spectral Band Distribution ({scene.bands.length} Bands)</span>
        </div>

        <table className="bands-table" aria-label="Spectral Bands Specification">
          <thead>
            <tr>
              <th>Band</th>
              <th>Name</th>
              <th>Wavelength</th>
              <th>GSD</th>
              <th>Domain</th>
            </tr>
          </thead>
          <tbody>
            {scene.bands.map((band) => (
              <tr key={band.id} title={band.description}>
                <td className="band-code">{band.id}</td>
                <td style={{ color: 'var(--text-primary)' }}>{band.name}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>
                  {band.centralWavelengthMicrons > 1000
                    ? `${(band.centralWavelengthMicrons / 10000).toFixed(2)} cm`
                    : `${band.centralWavelengthMicrons.toFixed(3)} µm`}
                </td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{band.spatialResolutionMeters}m</td>
                <td>
                  <span
                    style={{
                      fontSize: '10px',
                      padding: '1px 5px',
                      background: 'rgba(255, 255, 255, 0.05)',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {band.domain}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* STAC Endpoint Reference */}
      <div style={{ fontSize: '11px', color: 'var(--text-muted)', wordBreak: 'break-all' }}>
        <span>STAC URI: </span>
        <a
          href={scene.stacSelfHref}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--accent-cyan)', textDecoration: 'none' }}
          onClick={(e) => {
            e.preventDefault();
            alert(`Simulated STAC Item reference:\n${scene.stacSelfHref}`);
          }}
        >
          {scene.stacSelfHref}
        </a>
      </div>
    </div>
  );
};
