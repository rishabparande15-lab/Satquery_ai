import React, { useState } from 'react';
import {
  SatelliteScene,
  SearchFilterParams,
  AnalysisJob,
  AnalysisResult,
  MapLayerType,
} from '../../types/satellite';
import { QueryBar } from '../query/QueryBar';
import { SearchResultsPanel } from '../results/SearchResultsPanel';
import { MapWorkspace } from '../map/MapWorkspace';
import { SatelliteMetadataPanel } from '../results/SatelliteMetadataPanel';
import { AnalysisStatusPanel } from '../analysis/AnalysisStatusPanel';
import { ResultSummaryCard } from '../analysis/ResultSummaryCard';

interface DashboardViewProps {
  scenes: SatelliteScene[];
  selectedScene: SatelliteScene | null;
  onSelectScene: (scene: SatelliteScene) => void;
  filters: SearchFilterParams;
  onFilterChange: (filters: Partial<SearchFilterParams>) => void;
  onSubmitQuery: (query: string) => void;
  isSearching: boolean;
  searchError: string | null;
  onRetrySearch: () => void;
  onResetFilters: () => void;
  activeLayer: MapLayerType;
  onChangeLayer: (layer: MapLayerType) => void;
  analysisJob: AnalysisJob | null;
  analysisResult: AnalysisResult | null;
  isAnalyzing: boolean;
  onTriggerAnalysis: (scene?: SatelliteScene) => void;
  onSaveAnalysis: (result: AnalysisResult, scene: SatelliteScene, notes: string) => void;
  isCurrentResultSaved: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  scenes,
  selectedScene,
  onSelectScene,
  filters,
  onFilterChange,
  onSubmitQuery,
  isSearching,
  searchError,
  onRetrySearch,
  onResetFilters,
  activeLayer,
  onChangeLayer,
  analysisJob,
  analysisResult,
  isAnalyzing,
  onTriggerAnalysis,
  onSaveAnalysis,
  isCurrentResultSaved,
}) => {
  const [rightPanelTab, setRightPanelTab] = useState<'analysis' | 'metadata'>('analysis');

  return (
    <div className="dashboard-layout">
      {/* Left Panel: Query & Search Results */}
      <aside className="panel-left" aria-label="Catalog Search and Queries">
        <QueryBar
          filters={filters}
          onFilterChange={onFilterChange}
          onSubmitQuery={onSubmitQuery}
          isSearching={isSearching}
        />
        <SearchResultsPanel
          scenes={scenes}
          selectedScene={selectedScene}
          onSelectScene={onSelectScene}
          onAnalyzeScene={(scene) => onTriggerAnalysis(scene)}
          isLoading={isSearching}
          error={searchError}
          onRetry={onRetrySearch}
          onResetFilters={onResetFilters}
          isAnalyzing={isAnalyzing}
        />
      </aside>

      {/* Center Panel: Interactive Geospatial Map Workspace */}
      <MapWorkspace
        scene={selectedScene}
        activeLayer={activeLayer}
        onChangeLayer={onChangeLayer}
        onTriggerAnalysis={() => onTriggerAnalysis()}
        isAnalyzing={isAnalyzing}
      />

      {/* Right Panel: Analysis Telemetry & STAC Metadata */}
      <section className="panel-right" aria-label="Analysis Telemetry and Metadata">
        <div className="tab-row" role="tablist">
          <button
            className={`tab-btn ${rightPanelTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setRightPanelTab('analysis')}
            role="tab"
            aria-selected={rightPanelTab === 'analysis'}
          >
            AI Analysis
            {analysisJob?.status === 'processing' && (
              <span className="status-dot cyan" style={{ marginLeft: '6px' }} />
            )}
          </button>
          <button
            className={`tab-btn ${rightPanelTab === 'metadata' ? 'active' : ''}`}
            onClick={() => setRightPanelTab('metadata')}
            role="tab"
            aria-selected={rightPanelTab === 'metadata'}
          >
            STAC Metadata & Bands
          </button>
        </div>

        {rightPanelTab === 'analysis' ? (
          <div className="panel-content">
            <AnalysisStatusPanel job={analysisJob} />
            <ResultSummaryCard
              result={analysisResult}
              scene={selectedScene}
              onSaveAnalysis={onSaveAnalysis}
              isSaved={isCurrentResultSaved}
            />
          </div>
        ) : (
          <SatelliteMetadataPanel scene={selectedScene} />
        )}
      </section>
    </div>
  );
};
