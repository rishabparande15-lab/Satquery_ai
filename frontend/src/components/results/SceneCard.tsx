import React from 'react';
import { SatelliteScene } from '../../types/satellite';

interface SceneCardProps {
  scene: SatelliteScene;
  isSelected: boolean;
  onSelect: (scene: SatelliteScene) => void;
  onAnalyze: (scene: SatelliteScene) => void;
  isAnalyzing: boolean;
}

export const SceneCard: React.FC<SceneCardProps> = ({
  scene,
  isSelected,
  onSelect,
  onAnalyze,
  isAnalyzing,
}) => {
  const getMissionTagClass = () => {
    switch (scene.mission) {
      case 'Sentinel-1-SAR':
        return 'sar';
      case 'Landsat-8/9':
        return 'landsat';
      case 'PlanetScope':
        return 'planet';
      default:
        return '';
    }
  };

  const formattedDate = new Date(scene.acquisitionDate).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <article
      className={`scene-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(scene)}
      aria-label={`Satellite scene ${scene.title}`}
    >
      <div className="scene-card-header">
        <h4 className="scene-title">{scene.locationName}</h4>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          {scene.isRealData ? (
            <span
              className="environment-badge"
              style={{ fontSize: '9px', padding: '1px 5px', color: 'var(--accent-emerald)', borderColor: 'rgba(0, 214, 143, 0.3)', background: 'rgba(0, 214, 143, 0.1)' }}
            >
              LIVE STAC
            </span>
          ) : (
            <span
              className="environment-badge"
              style={{ fontSize: '9px', padding: '1px 5px', color: 'var(--text-muted)', borderColor: 'var(--border-subtle)' }}
            >
              MOCK
            </span>
          )}
          <span className={`mission-tag ${getMissionTagClass()}`}>{scene.mission}</span>
        </div>
      </div>

      <div className="scene-meta-row">
        <span>📅 {formattedDate}</span>
        <span>•</span>
        <span>☁️ {scene.cloudCoverPercent.toFixed(1)}% Cloud</span>
        <span>•</span>
        <span>📐 {scene.spatialResolutionMeters}m GSD</span>
      </div>

      <div className="scene-actions-row">
        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
          {scene.platformId} [{scene.sensor}]
        </span>
        <button
          className="btn-analyze"
          onClick={(e) => {
            e.stopPropagation();
            onAnalyze(scene);
          }}
          disabled={isAnalyzing}
          title="Run NDVI processing on this Sentinel-2 scene"
        >
          {isAnalyzing && isSelected ? 'Analyzing...' : 'Analyze'}
        </button>
      </div>
    </article>
  );
};
