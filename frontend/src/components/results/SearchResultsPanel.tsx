import React from 'react';
import { SatelliteScene } from '../../types/satellite';
import { SceneCard } from './SceneCard';
import { LoadingSkeleton } from '../common/LoadingSkeleton';
import { EmptyState } from '../common/EmptyState';
import { ErrorBanner } from '../common/ErrorBanner';

interface SearchResultsPanelProps {
  scenes: SatelliteScene[];
  selectedScene: SatelliteScene | null;
  onSelectScene: (scene: SatelliteScene) => void;
  onAnalyzeScene: (scene: SatelliteScene) => void;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  onResetFilters: () => void;
  isAnalyzing: boolean;
}

export const SearchResultsPanel: React.FC<SearchResultsPanelProps> = ({
  scenes,
  selectedScene,
  onSelectScene,
  onAnalyzeScene,
  isLoading,
  error,
  onRetry,
  onResetFilters,
  isAnalyzing,
}) => {
  return (
    <section className="results-list" aria-label="Satellite Search Results">
      <div className="panel-header" style={{ padding: '4px 2px 8px' }}>
        <span className="panel-title">
          <span>Catalog Results</span>
          <span className="environment-badge" style={{ fontSize: '10px' }}>
            {scenes.length} Granules
          </span>
        </span>
      </div>

      {error && <ErrorBanner message={error} onRetry={onRetry} />}

      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : scenes.length === 0 ? (
        <EmptyState
          iconType="search"
          title="No Matching Satellite Scenes"
          description="Try broadening your search keywords, increasing allowed cloud coverage, or changing mission filters."
          actionLabel="Reset Search Filters"
          onAction={onResetFilters}
        />
      ) : (
        scenes.map((scene) => (
          <SceneCard
            key={scene.id}
            scene={scene}
            isSelected={selectedScene?.id === scene.id}
            onSelect={onSelectScene}
            onAnalyze={onAnalyzeScene}
            isAnalyzing={isAnalyzing}
          />
        ))
      )}
    </section>
  );
};
