import React from 'react';
import { SearchFilterParams, SupportedMission } from '../../types/satellite';
import { SAMPLE_QUERIES } from '../../services/mockData';

interface QueryBarProps {
  filters: SearchFilterParams;
  onFilterChange: (newFilters: Partial<SearchFilterParams>) => void;
  onSubmitQuery: (query: string) => void;
  isSearching: boolean;
}

export const QueryBar: React.FC<QueryBarProps> = ({
  filters,
  onFilterChange,
  onSubmitQuery,
  isSearching,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onSubmitQuery(filters.queryText);
    }
  };

  const handleChipClick = (queryText: string) => {
    onFilterChange({ queryText });
    onSubmitQuery(queryText);
  };

  return (
    <section className="query-box" aria-label="Natural Language Query Controls">
      <div className="query-input-wrapper">
        <input
          type="text"
          className="query-input"
          placeholder="Ask about Earth observation data (e.g., NDVI in Amazon, water quality in Rotterdam)..."
          value={filters.queryText}
          onChange={(e) => onFilterChange({ queryText: e.target.value })}
          onKeyDown={handleKeyDown}
          aria-label="Satellite query text input"
        />
        <button
          className="query-submit-btn"
          onClick={() => onSubmitQuery(filters.queryText)}
          disabled={isSearching}
          title="Search satellite catalog"
          aria-label="Submit search query"
        >
          {isSearching ? (
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
            </svg>
          )}
        </button>
      </div>

      {/* Filter Row */}
      <div className="filter-row">
        <select
          className="select-filter"
          value={filters.mission}
          onChange={(e) =>
            onFilterChange({ mission: e.target.value as SupportedMission | 'All' })
          }
          aria-label="Mission Filter"
        >
          <option value="All">All Missions</option>
          <option value="Sentinel-2">Sentinel-2 (MSI)</option>
          <option value="Landsat-8/9">Landsat 8/9 (OLI-2)</option>
          <option value="Sentinel-1-SAR">Sentinel-1 (SAR)</option>
          <option value="PlanetScope">PlanetScope (3m)</option>
        </select>

        <select
          className="select-filter"
          value={filters.resolution || 'all'}
          onChange={(e) =>
            onFilterChange({
              resolution: e.target.value as 'all' | '10m' | '15m' | '30m',
            })
          }
          aria-label="Resolution Filter"
        >
          <option value="all">Any Resolution</option>
          <option value="10m">&le; 10m Ground Sample</option>
          <option value="15m">&le; 15m Ground Sample</option>
          <option value="30m">&le; 30m Ground Sample</option>
        </select>

        <div className="slider-container" title="Maximum allowed cloud coverage in scene">
          <span>Cloud: &le;{filters.maxCloudCover}%</span>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={filters.maxCloudCover}
            onChange={(e) => onFilterChange({ maxCloudCover: Number(e.target.value) })}
            aria-label="Maximum Cloud Cover percentage"
          />
        </div>
      </div>

      {/* Sample Queries */}
      <div className="query-chips">
        <span className="chip-label">Sample Scientific Queries:</span>
        <div className="chips-list">
          {SAMPLE_QUERIES.slice(0, 3).map((sq, idx) => (
            <button
              key={idx}
              type="button"
              className="query-chip"
              onClick={() => handleChipClick(sq)}
            >
              {sq}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};
