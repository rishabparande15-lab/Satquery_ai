import React, { useEffect, useRef, useState } from 'react';
import { MapLayerType, SatelliteScene } from '../../types/satellite';

interface LiveScenePreviewProps {
  scene: SatelliteScene | null;
  activeLayer: MapLayerType;
  onChangeLayer: (layer: MapLayerType) => void;
  onTriggerAnalysis: () => void;
  isAnalyzing: boolean;
}

export const LiveScenePreview: React.FC<LiveScenePreviewProps> = ({
  scene,
  activeLayer,
  onChangeLayer,
  onTriggerAnalysis,
  isAnalyzing,
}) => {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panOffset, setPanOffset] = useState({ x: 0, y: 0 });
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [previewFailed, setPreviewFailed] = useState(false);
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setPreviewFailed(false);
  }, [scene?.id]);

  const canShowPreview = Boolean(scene?.previewUrl) && !previewFailed;

  const handleMouseMove = (event: React.MouseEvent) => {
    if (isPanning) {
      setPanOffset({ x: event.clientX - dragStart.x, y: event.clientY - dragStart.y });
    }
    if (scene && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const [minLon, minLat, maxLon, maxLat] = scene.boundingBox;
      const relativeX = (event.clientX - rect.left) / rect.width;
      const relativeY = (event.clientY - rect.top) / rect.height;
      setCursorCoords({
        lon: minLon + relativeX * (maxLon - minLon),
        lat: maxLat - relativeY * (maxLat - minLat),
      });
    }
  };

  return (
    <section
      className="panel-center"
      ref={containerRef}
      onMouseDown={(event) => {
        if (event.button === 0) {
          setIsPanning(true);
          setDragStart({ x: event.clientX - panOffset.x, y: event.clientY - panOffset.y });
        }
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={() => setIsPanning(false)}
      onMouseLeave={() => setIsPanning(false)}
      style={{ cursor: isPanning ? 'grabbing' : 'crosshair' }}
      aria-label="Satellite scene preview"
    >
      <div className="map-simulation-watermark">
        <span className={`status-dot ${canShowPreview ? 'emerald' : 'cyan'}`} />
        <span>{canShowPreview ? 'Live STAC natural-color preview' : 'STAC scene footprint'}</span>
      </div>
      <div className="map-layer-controls" aria-label="Available visual layers">
        <button className={`layer-btn ${activeLayer === 'true_color' ? 'active' : ''}`} onClick={() => onChangeLayer('true_color')} title="Natural-color preview supplied by the selected STAC item">True Color</button>
        <button className="layer-btn" disabled title="This phase exposes NDVI statistics, not a rendered raster layer.">NDVI Statistics</button>
      </div>
      <div className="map-viewport">
        {canShowPreview ? (
          <img
            key={scene?.id}
            className="scene-preview-image"
            src={scene?.previewUrl ?? undefined}
            alt={`Natural-color preview for ${scene?.title ?? 'selected satellite scene'}`}
            onError={() => setPreviewFailed(true)}
            style={{ transform: `translate(${panOffset.x}px, ${panOffset.y}px) scale(${zoomLevel})` }}
          />
        ) : (
          <div className="scene-preview-unavailable">
            <strong>{scene ? 'Preview asset unavailable' : 'Select a live Sentinel-2 scene'}</strong>
            <span>{scene ? 'This STAC item has no browser-renderable preview. Its real metadata and NDVI workflow remain available.' : 'Search the live STAC catalog to view a scene footprint and calculate bounded-window NDVI.'}</span>
          </div>
        )}
        {scene && <div className="scene-footprint-label">{scene.platformId} · {scene.acquisitionDate.slice(0, 10)}</div>}
      </div>
      <div className="map-hud-footer">
        <div className="hud-pill">
          <span>LAT/LON: {cursorCoords ? `${cursorCoords.lat.toFixed(4)}°, ${cursorCoords.lon.toFixed(4)}°` : scene ? `${scene.centerCoordinates.lat.toFixed(4)}°, ${scene.centerCoordinates.lon.toFixed(4)}°` : '--, --'}</span>
          <span style={{ color: 'var(--border-muted)' }}>|</span>
          <span>{scene ? `${scene.spatialResolutionMeters} m source resolution` : 'Select a scene'}</span>
          <span style={{ color: 'var(--border-muted)' }}>|</span>
          <span>ZOOM: {(zoomLevel * 100).toFixed(0)}%</span>
        </div>
        <div className="map-nav-tools">
          <button className="btn-analyze" onClick={onTriggerAnalysis} disabled={isAnalyzing || !scene} title="Calculate NDVI from the selected scene's B04 and B08 assets">{isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}</button>
          <button className="map-tool-btn" onClick={() => setZoomLevel((value) => Math.min(value + 0.3, 3))} title="Zoom in">+</button>
          <button className="map-tool-btn" onClick={() => setZoomLevel((value) => Math.max(value - 0.3, 0.7))} title="Zoom out">-</button>
          <button className="map-tool-btn" onClick={() => { setZoomLevel(1); setPanOffset({ x: 0, y: 0 }); }} title="Reset view">⟲</button>
        </div>
      </div>
    </section>
  );
};
