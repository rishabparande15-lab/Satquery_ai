import React, { useState, useRef } from 'react';
import { SatelliteScene, MapLayerType } from '../../types/satellite';

interface MapWorkspaceProps {
  scene: SatelliteScene | null;
  activeLayer: MapLayerType;
  onChangeLayer: (layer: MapLayerType) => void;
  onTriggerAnalysis: () => void;
  isAnalyzing: boolean;
}

export const MapWorkspace: React.FC<MapWorkspaceProps> = ({
  scene,
  activeLayer,
  onChangeLayer,
  onTriggerAnalysis,
  isAnalyzing,
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lon: number } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsPanning(true);
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isPanning) {
      setPanOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }

    if (scene && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const relX = (e.clientX - rect.left) / rect.width;
      const relY = (e.clientY - rect.top) / rect.height;

      // Map normalized coordinates into scene bounding box [minLon, minLat, maxLon, maxLat]
      const [minLon, minLat, maxLon, maxLat] = scene.boundingBox;
      const lon = minLon + relX * (maxLon - minLon);
      const lat = maxLat - relY * (maxLat - minLat);

      setCursorCoords({ lat, lon });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
  };

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.3, 3.0));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.3, 0.7));
  const handleReset = () => {
    setZoomLevel(1);
    setPanOffset({ x: 0, y: 0 });
  };

  // Helper color mappings for simulated layers
  const getLayerPalette = () => {
    switch (activeLayer) {
      case 'false_color_ir':
        return {
          water: '#0a192f',
          land: '#be123c',
          urban: '#64748b',
          accent: '#f43f5e',
          stroke: '#fda4af',
        };
      case 'ndvi':
        return {
          water: '#0284c7',
          land: '#15803d',
          urban: '#a1a1aa',
          accent: '#22c55e',
          stroke: '#86efac',
        };
      case 'sar_amplitude':
        return {
          water: '#030712',
          land: '#374151',
          urban: '#f3f4f6',
          accent: '#e5e7eb',
          stroke: '#9ca3af',
        };
      case 'thermal':
        return {
          water: '#1e3a8a',
          land: '#ea580c',
          urban: '#f97316',
          accent: '#fbbf24',
          stroke: '#fed7aa',
        };
      case 'true_color':
      default:
        return {
          water: '#0c2d48',
          land: '#2d4a22',
          urban: '#475569',
          accent: '#14b8a6',
          stroke: '#5eead4',
        };
    }
  };

  const palette = getLayerPalette();

  return (
    <section
      className="panel-center"
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{ cursor: isPanning ? 'grabbing' : 'crosshair' }}
      aria-label="Map Workspace Viewport"
    >
      {/* Simulation Watermark */}
      <div className="map-simulation-watermark">
        <span className="status-dot cyan" />
        <span>Simulated Geospatial Canvas (Preview Only)</span>
      </div>

      {/* Layer Controls */}
      <div className="map-layer-controls">
        <button
          className={`layer-btn ${activeLayer === 'true_color' ? 'active' : ''}`}
          onClick={() => onChangeLayer('true_color')}
          title="Natural color RGB composite"
        >
          True Color
        </button>
        <button
          className={`layer-btn ${activeLayer === 'false_color_ir' ? 'active' : ''}`}
          onClick={() => onChangeLayer('false_color_ir')}
          title="Color Infrared (NIR/Red/Green) for vegetation contrast"
        >
          Color IR
        </button>
        <button
          className={`layer-btn ${activeLayer === 'ndvi' ? 'active' : ''}`}
          onClick={() => onChangeLayer('ndvi')}
          title="Normalized Difference Vegetation Index heat map"
        >
          NDVI
        </button>
        <button
          className={`layer-btn ${activeLayer === 'sar_amplitude' ? 'active' : ''}`}
          onClick={() => onChangeLayer('sar_amplitude')}
          title="Radar microwave backscatter amplitude (dB)"
        >
          SAR
        </button>
        <button
          className={`layer-btn ${activeLayer === 'thermal' ? 'active' : ''}`}
          onClick={() => onChangeLayer('thermal')}
          title="Longwave thermal infrared surface emission"
        >
          Thermal
        </button>
      </div>

      {/* Center Crosshair */}
      <div className="map-crosshair">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
          <line x1="12" y1="2" x2="12" y2="8" />
          <line x1="12" y1="16" x2="12" y2="22" />
          <line x1="2" y1="12" x2="8" y2="12" />
          <line x1="16" y1="12" x2="22" y2="12" />
          <circle cx="12" cy="12" r="4" strokeWidth="0.75" />
        </svg>
      </div>

      {/* Interactive Canvas Rendering */}
      <div className="map-viewport">
        <svg
          className="map-svg-canvas"
          viewBox="0 0 800 600"
          preserveAspectRatio="xMidYMid slice"
        >
          <defs>
            {/* Grid Pattern */}
            <pattern id="grid" width="80" height="80" patternUnits="userSpaceOnUse">
              <path
                d="M 80 0 L 0 0 0 80"
                fill="none"
                stroke="rgba(255, 255, 255, 0.05)"
                strokeWidth="0.5"
              />
            </pattern>
            {/* Dense Tick Subgrid */}
            <pattern id="subgrid" width="16" height="16" patternUnits="userSpaceOnUse">
              <path
                d="M 16 0 L 0 0 0 16"
                fill="none"
                stroke="rgba(255, 255, 255, 0.02)"
                strokeWidth="0.5"
              />
            </pattern>
          </defs>

          {/* Background Grid */}
          <rect width="100%" height="100%" fill="#06090e" />
          <rect width="100%" height="100%" fill="url(#subgrid)" />
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Scaled Scene Graphics */}
          <g
            transform={`translate(${400 + panOffset.x}, ${300 + panOffset.y}) scale(${zoomLevel}) translate(-400, -300)`}
          >
            {/* Water Basemap Base */}
            <rect x="60" y="50" width="680" height="500" rx="4" fill={palette.water} />

            {/* Render Biome Geometry depending on scene type */}
            {scene?.thumbnailSvgType === 'urban_port' && (
              <g>
                {/* Coastal landmass */}
                <path
                  d="M 60 50 L 380 50 Q 420 180 340 320 Q 300 420 480 550 L 60 550 Z"
                  fill={palette.land}
                  stroke={palette.stroke}
                  strokeWidth="1.5"
                />
                {/* Port Piers / Breakwaters */}
                <rect x="360" y="160" width="180" height="24" rx="2" fill={palette.urban} />
                <rect x="390" y="220" width="160" height="20" rx="2" fill={palette.urban} />
                <rect x="340" y="280" width="200" height="26" rx="2" fill={palette.urban} />
                {/* Vessels in fairway */}
                <circle cx="560" cy="140" r="4" fill={palette.accent} />
                <circle cx="610" cy="200" r="5" fill={palette.accent} />
                <circle cx="580" cy="260" r="4" fill={palette.accent} />
                <circle cx="640" cy="310" r="6" fill={palette.accent} />
              </g>
            )}

            {scene?.thumbnailSvgType === 'rainforest' && (
              <g>
                {/* Continuous forest canopy */}
                <rect x="60" y="50" width="680" height="500" fill={palette.land} />
                {/* Meandering Amazon river */}
                <path
                  d="M 60 140 Q 220 80 340 220 T 580 360 T 740 320"
                  fill="none"
                  stroke={palette.water}
                  strokeWidth="54"
                  strokeLinecap="round"
                />
                <path
                  d="M 340 220 Q 400 380 480 550"
                  fill="none"
                  stroke={palette.water}
                  strokeWidth="24"
                  strokeLinecap="round"
                />
                {/* Simulated clearings / roads */}
                <path
                  d="M 160 380 L 320 380 L 320 500"
                  fill="none"
                  stroke={palette.urban}
                  strokeWidth="4"
                  strokeDasharray="6,4"
                />
                <rect x="180" y="400" width="80" height="60" fill={palette.accent} opacity="0.6" />
              </g>
            )}

            {scene?.thumbnailSvgType === 'agricultural' && (
              <g>
                {/* Agricultural fields grid */}
                <rect x="60" y="50" width="680" height="500" fill={palette.land} />
                {/* Nile river stream */}
                <path
                  d="M 400 550 L 400 320 Q 360 200 240 50 M 400 320 Q 440 200 560 50"
                  fill="none"
                  stroke={palette.water}
                  strokeWidth="28"
                />
                {/* Field boundaries */}
                {Array.from({ length: 7 }).map((_, i) => (
                  <line
                    key={`h-${i}`}
                    x1="100"
                    y1={100 + i * 60}
                    x2="700"
                    y2={100 + i * 60}
                    stroke="rgba(0,0,0,0.25)"
                    strokeWidth="2"
                  />
                ))}
                {Array.from({ length: 8 }).map((_, j) => (
                  <line
                    key={`v-${j}`}
                    x1={120 + j * 70}
                    y1="80"
                    x2={120 + j * 70}
                    y2="520"
                    stroke="rgba(0,0,0,0.25)"
                    strokeWidth="2"
                  />
                ))}
              </g>
            )}

            {scene?.thumbnailSvgType === 'bay_valley' && (
              <g>
                {/* Bay water inlet */}
                <rect x="60" y="50" width="680" height="500" fill={palette.land} />
                <path
                  d="M 320 50 Q 240 180 260 360 Q 290 480 440 550 L 520 550 Q 420 400 440 260 Q 460 120 400 50 Z"
                  fill={palette.water}
                  stroke={palette.stroke}
                  strokeWidth="1.5"
                />
                {/* Urban infrastructure bridges */}
                <line x1="260" y1="200" x2="430" y2="180" stroke={palette.urban} strokeWidth="5" />
                <line x1="270" y1="360" x2="440" y2="380" stroke={palette.urban} strokeWidth="5" />
              </g>
            )}

            {scene?.thumbnailSvgType === 'glacial_ice' && (
              <g>
                <rect x="60" y="50" width="680" height="500" fill={palette.land} />
                {/* Glacial crevasse streaks */}
                <path
                  d="M 120 80 Q 280 240 420 480 M 180 60 Q 340 220 480 460 M 240 50 Q 400 200 540 440"
                  fill="none"
                  stroke={palette.stroke}
                  strokeWidth="3"
                  strokeDasharray="14,6"
                />
                {/* Ice mélange calving front */}
                <circle cx="480" cy="460" r="28" fill={palette.accent} opacity="0.5" />
              </g>
            )}

            {/* Satellite Footprint Bounding Box overlay */}
            <rect
              x="120"
              y="90"
              width="560"
              height="420"
              fill="none"
              stroke="var(--accent-cyan)"
              strokeWidth="1.5"
              strokeDasharray="6,4"
            />
            {/* Footprint Corner Crosses */}
            <circle cx="120" cy="90" r="3" fill="var(--accent-cyan)" />
            <circle cx="680" cy="90" r="3" fill="var(--accent-cyan)" />
            <circle cx="120" cy="510" r="3" fill="var(--accent-cyan)" />
            <circle cx="680" cy="510" r="3" fill="var(--accent-cyan)" />

            {/* Footprint Title */}
            {scene && (
              <text
                x="130"
                y="110"
                fill="var(--accent-cyan)"
                fontSize="11"
                fontFamily="var(--font-mono)"
                fontWeight="600"
              >
                SWATH: {scene.platformId} [{scene.processingLevel}]
              </text>
            )}
          </g>
        </svg>
      </div>

      {/* Map HUD Footer with coordinates and pan/zoom */}
      <div className="map-hud-footer">
        <div className="hud-pill">
          <span>
            LAT/LON:{' '}
            {cursorCoords
              ? `${cursorCoords.lat.toFixed(4)}°, ${cursorCoords.lon.toFixed(4)}°`
              : scene
              ? `${scene.centerCoordinates.lat.toFixed(4)}°, ${scene.centerCoordinates.lon.toFixed(4)}°`
              : '--, --'}
          </span>
          <span style={{ color: 'var(--border-muted)' }}>|</span>
          <span>SCALE: ~10 km / DIV</span>
          <span style={{ color: 'var(--border-muted)' }}>|</span>
          <span>ZOOM: {(zoomLevel * 100).toFixed(0)}%</span>
        </div>

        <div className="map-nav-tools">
          <button
            className="btn-analyze"
            onClick={onTriggerAnalysis}
            disabled={isAnalyzing || !scene}
            title="Execute simulated AI evidence pipeline"
          >
            <svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" />
            </svg>
            <span>{isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}</span>
          </button>
          <button className="map-tool-btn" onClick={handleZoomIn} title="Zoom in">
            +
          </button>
          <button className="map-tool-btn" onClick={handleZoomOut} title="Zoom out">
            -
          </button>
          <button className="map-tool-btn" onClick={handleReset} title="Reset view">
            ⟲
          </button>
        </div>
      </div>
    </section>
  );
};
