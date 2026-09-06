import { useState, useEffect, useCallback } from 'react';
import {
  SatelliteScene,
  SearchFilterParams,
  AnalysisJob,
  AnalysisResult,
  QueryHistoryItem,
  SavedAnalysis,
  BackendHealth,
  ActiveNavTab,
  MapLayerType,
} from './types/satellite';
import { apiClient } from './services/apiClient';
import { Header } from './components/common/Header';
import { Sidebar } from './components/common/Sidebar';
import { DashboardView } from './components/views/DashboardView';
import { HistoryView } from './components/views/HistoryView';
import { SavedAnalysesView } from './components/views/SavedAnalysesView';
import { SettingsView } from './components/views/SettingsView';

export function App() {
  // Navigation State
  const [activeTab, setActiveTab] = useState<ActiveNavTab>('dashboard');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // Search & Catalog State
  const [filters, setFilters] = useState<SearchFilterParams>({
    queryText: '',
    mission: 'All',
    maxCloudCover: 20,
    resolution: 'all',
  });
  const [scenes, setScenes] = useState<SatelliteScene[]>([]);
  const [selectedScene, setSelectedScene] = useState<SatelliteScene | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Map Layer State
  const [activeLayer, setActiveLayer] = useState<MapLayerType>('true_color');

  // Analysis Pipeline State
  const [analysisJob, setAnalysisJob] = useState<AnalysisJob | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // History & Saved Records
  const [history, setHistory] = useState<QueryHistoryItem[]>([]);
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);

  // Backend Health Telemetry & Operational Mode
  const [operationalMode, setOperationalMode] = useState<'live' | 'simulated'>('live');
  const [backendHealth, setBackendHealth] = useState<BackendHealth>({
    status: 'offline',
    service: 'Initializing...',
    lastChecked: new Date().toISOString(),
    message: 'Probing API...',
  });
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  // Check Backend Health
  const probeHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    const health = await apiClient.checkBackendHealth();
    setBackendHealth(health);
    setIsCheckingHealth(false);
  }, []);

  const handleSetOperationalMode = (mode: 'live' | 'simulated') => {
    setOperationalMode(mode);
    apiClient.setMode(mode);
    probeHealth();
  };


  // Execute Catalog Search
  const executeSearch = useCallback(
    async (currentFilters: SearchFilterParams) => {
      setIsSearching(true);
      setSearchError(null);

      try {
        const results = await apiClient.searchScenes(currentFilters);
        setScenes(results);

        // Keep selected scene if still in results, otherwise pick the first one
        if (results.length > 0) {
          if (!selectedScene || !results.some((s) => s.id === selectedScene.id)) {
            setSelectedScene(results[0]);
          }
        } else {
          setSelectedScene(null);
        }

        // Record query to history if user provided a query string
        if (currentFilters.queryText.trim()) {
          const newHist = apiClient.addQueryToHistory({
            query: currentFilters.queryText.trim(),
            locationName: results[0]?.locationName || 'Global Search',
            missionFilter: currentFilters.mission,
            resultCount: results.length,
          });
          setHistory((prev) => [newHist, ...prev.filter((h) => h.query !== newHist.query)]);
        }
      } catch (err: unknown) {
        setSearchError((err as Error).message || 'Failed to search satellite catalog.');
      } finally {
        setIsSearching(false);
      }
    },
    [selectedScene]
  );

  // Initial Data Load
  useEffect(() => {
    probeHealth();
    setHistory(apiClient.getQueryHistory());
    setSavedAnalyses(apiClient.getSavedAnalyses());

    // Perform initial search to populate workspace
    executeSearch({
      queryText: '',
      mission: 'All',
      maxCloudCover: 20,
      resolution: 'all',
    });
  }, [probeHealth, executeSearch]);

  // Handle Query Submission from QueryBar
  const handleQuerySubmit = (queryText: string) => {
    const updatedFilters = { ...filters, queryText };
    setFilters(updatedFilters);
    executeSearch(updatedFilters);
  };

  // Handle Filter Adjustments
  const handleFilterChange = (newFilters: Partial<SearchFilterParams>) => {
    const updated = { ...filters, ...newFilters };
    setFilters(updated);
    executeSearch(updated);
  };

  // Trigger Simulated AI Analysis Pipeline
  const handleTriggerAnalysis = async (targetScene?: SatelliteScene) => {
    const sceneToAnalyze = targetScene || selectedScene;
    if (!sceneToAnalyze || isAnalyzing) return;

    setIsAnalyzing(true);
    setAnalysisResult(null);

    const queryForAnalysis =
      filters.queryText.trim() || `Biophysical analysis for ${sceneToAnalyze.locationName}`;

    try {
      const result = await apiClient.runAnalysisPipeline(
        sceneToAnalyze,
        queryForAnalysis,
        (updatedJob) => {
          setAnalysisJob({ ...updatedJob });
        }
      );
      setAnalysisResult(result);
    } catch (err: unknown) {
      alert((err as Error).message || 'Analysis pipeline encountered an error.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Save Analysis Bookmark
  const handleSaveAnalysis = (
    result: AnalysisResult,
    scene: SatelliteScene,
    notes: string
  ) => {
    const saved = apiClient.saveAnalysis(result, scene, notes);
    setSavedAnalyses((prev) => [saved, ...prev.filter((s) => s.sceneId !== scene.id)]);
  };

  // Remove Saved Bookmark
  const handleRemoveSaved = (id: string) => {
    apiClient.removeSavedAnalysis(id);
    setSavedAnalyses((prev) => prev.filter((s) => s.id !== id));
  };

  // Clear Query History
  const handleClearHistory = () => {
    apiClient.clearHistory();
    setHistory([]);
  };

  // Open Saved Scene in Workspace
  const handleOpenSavedScene = (sceneId: string) => {
    const found = scenes.find((s) => s.id === sceneId);
    if (found) {
      setSelectedScene(found);
    }
    setActiveTab('dashboard');
  };

  // Re-run Query from History
  const handleReRunQuery = (queryText: string) => {
    const updated = { ...filters, queryText };
    setFilters(updated);
    setActiveTab('dashboard');
    executeSearch(updated);
  };

  const isCurrentResultSaved = Boolean(
    analysisResult && savedAnalyses.some((s) => s.sceneId === analysisResult.sceneId)
  );

  return (
    <div className="app-container">
      {/* Primary Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />

      {/* Main Screen Viewport */}
      <div className="main-viewport">
        {/* Top Telemetry Header */}
        <Header
          selectedScene={selectedScene}
          backendHealth={backendHealth}
          onRefreshHealth={probeHealth}
          operationalMode={operationalMode}
          onToggleMode={() =>
            handleSetOperationalMode(operationalMode === 'live' ? 'simulated' : 'live')
          }
        />

        {/* Dynamic View Display */}
        {activeTab === 'dashboard' && (
          <DashboardView
            scenes={scenes}
            selectedScene={selectedScene}
            onSelectScene={setSelectedScene}
            filters={filters}
            onFilterChange={handleFilterChange}
            onSubmitQuery={handleQuerySubmit}
            isSearching={isSearching}
            searchError={searchError}
            onRetrySearch={() => executeSearch(filters)}
            onResetFilters={() => {
              const reset: SearchFilterParams = {
                queryText: '',
                mission: 'All',
                maxCloudCover: 20,
                resolution: 'all',
              };
              setFilters(reset);
              executeSearch(reset);
            }}
            activeLayer={activeLayer}
            onChangeLayer={setActiveLayer}
            analysisJob={analysisJob}
            analysisResult={analysisResult}
            isAnalyzing={isAnalyzing}
            onTriggerAnalysis={handleTriggerAnalysis}
            onSaveAnalysis={handleSaveAnalysis}
            isCurrentResultSaved={isCurrentResultSaved}
          />
        )}

        {activeTab === 'history' && (
          <HistoryView
            history={history}
            onSelectQuery={handleReRunQuery}
            onClearHistory={handleClearHistory}
          />
        )}

        {activeTab === 'saved' && (
          <SavedAnalysesView
            savedList={savedAnalyses}
            onSelectSaved={handleOpenSavedScene}
            onRemoveSaved={handleRemoveSaved}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsView
            backendHealth={backendHealth}
            onRefreshHealth={probeHealth}
            isCheckingHealth={isCheckingHealth}
            onClearHistory={handleClearHistory}
            operationalMode={operationalMode}
            onSetOperationalMode={handleSetOperationalMode}
          />
        )}

        {/* Mobile Bottom Navigation Bar */}
        <nav className="mobile-bottom-nav" aria-label="Mobile Navigation">
          <button
            className={`mobile-nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <span>🗺️</span>
            <span>Workspace</span>
          </button>
          <button
            className={`mobile-nav-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <span>📜</span>
            <span>History</span>
          </button>
          <button
            className={`mobile-nav-btn ${activeTab === 'saved' ? 'active' : ''}`}
            onClick={() => setActiveTab('saved')}
          >
            <span>🔖</span>
            <span>Saved</span>
          </button>
          <button
            className={`mobile-nav-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <span>⚙️</span>
            <span>Health</span>
          </button>
        </nav>
      </div>
    </div>
  );
}

export default App;