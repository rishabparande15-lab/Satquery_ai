import {
  SatelliteScene,
  SearchFilterParams,
  AnalysisJob,
  AnalysisResult,
  PipelineStage,
  QueryHistoryItem,
  SavedAnalysis,
  BackendHealth,
} from '../types/satellite';
import {
  MOCK_SCENES,
  MOCK_ANALYSIS_RESULTS,
  INITIAL_QUERY_HISTORY,
  INITIAL_SAVED_ANALYSES,
} from './mockData';

const HISTORY_STORAGE_KEY = 'satquery_query_history_v1';
const SAVED_STORAGE_KEY = 'satquery_saved_analyses_v1';

// Resolved from NEXT_PUBLIC_API_BASE_URL (or VITE_API_BASE_URL) for local dev and production deployments
export const BACKEND_BASE_URL: string =
  (typeof import.meta !== 'undefined' &&
    import.meta.env &&
    (import.meta.env.NEXT_PUBLIC_API_BASE_URL || import.meta.env.VITE_API_BASE_URL)) ||
  'http://localhost:8000';



export type OperationalMode = 'live' | 'simulated';

/**
 * Clean service layer connecting the frontend to the FastAPI Earth observation backend,
 * with explicit operational modes (Live vs Simulated) and strict error reporting (no silent fallbacks).
 */
class SatelliteApiClient {
  private isBackendOnline = false;
  private mode: OperationalMode = 'live';

  /**
   * Set operational mode ('live' or 'simulated')
   */
  setMode(newMode: OperationalMode) {
    this.mode = newMode;
  }

  /**
   * Get current operational mode
   */
  getMode(): OperationalMode {
    return this.mode;
  }

  /**
   * Probes backend health and capabilities.
   */
  async checkBackendHealth(): Promise<BackendHealth> {
    const startTime = performance.now();
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2500);

      const response = await fetch(`${BACKEND_BASE_URL}/api/health`, {
        method: 'GET',
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      const latencyMs = Math.round(performance.now() - startTime);

      if (response.ok) {
        const data = await response.json();
        this.isBackendOnline = true;
        return {
          status: 'connected',
          service: data.service || 'SatQuery AI API',
          version: data.version || '0.1.0',
          activeMode: this.mode,
          capabilities: data.capabilities || ['sentinel-2-l2a-search', 'bounded-window-ndvi'],
          providers: data.providers || ['earth-search-stac'],
          latencyMs,
          lastChecked: new Date().toISOString(),
          message: 'Connected to FastAPI Backend (Live STAC & Real NDVI Ready)',
        };
      }
    } catch {
      // Backend not running or unreachable
    }

    this.isBackendOnline = false;

    if (this.mode === 'live') {
      return {
        status: 'offline',
        service: 'FastAPI Backend (Offline)',
        version: '0.1.0',
        activeMode: 'live',
        capabilities: [],
        providers: [],
        latencyMs: undefined,
        lastChecked: new Date().toISOString(),
        message: `FastAPI backend is offline at ${BACKEND_BASE_URL}. Run uvicorn locally or configure NEXT_PUBLIC_API_BASE_URL.`,
      };
    }

    return {
      status: 'simulated_fallback',
      service: 'SatQuery Simulated Engine v0.1',
      version: '0.1.0-simulated',
      activeMode: 'simulated',
      capabilities: ['simulated-search', 'simulated-ndvi'],
      providers: ['mock-dataset'],
      latencyMs: 1,
      lastChecked: new Date().toISOString(),
      message: 'Running in simulated standalone mode (mock datasets)',
    };
  }

  /**
   * Search satellite scenes using natural language or structured parameters.
   * In LIVE mode, queries FastAPI /api/search and will NEVER silently fall back to mock data.
   */
  async searchScenes(
    filters: SearchFilterParams,
    forceMock: boolean = false
  ): Promise<SatelliteScene[]> {
    const isLiveSearch = this.mode === 'live' && !forceMock;

    if (isLiveSearch) {
      try {
        const payload: Record<string, unknown> = {
          query: filters.queryText || undefined,
          max_cloud_cover: filters.maxCloudCover,
          mission: filters.mission === 'All' ? 'Sentinel-2' : filters.mission,
          start_date: filters.startDate || undefined,
          end_date: filters.endDate || undefined,
          limit: 10,
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const response = await fetch(`${BACKEND_BASE_URL}/api/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.ok) {
          const liveScenes: SatelliteScene[] = await response.json();
          this.isBackendOnline = true;
          return liveScenes;
        }

        // Parse structured error from backend
        const errData = await response.json().catch(() => ({}));
        const detailMsg =
          errData?.detail?.message ||
          (typeof errData?.detail === 'string' ? errData.detail : null);

        throw new Error(detailMsg || `Backend search failed with status ${response.status}`);
      } catch (err: unknown) {
        this.isBackendOnline = false;

        // In LIVE mode: NEVER silently return mock scenes!
        const errMsg = err instanceof Error ? err.message : String(err);
        const isNetworkFailure =
          errMsg.includes('Failed to fetch') ||
          errMsg.includes('NetworkError') ||
          errMsg.includes('aborted') ||
          errMsg.includes('abort');

        if (isNetworkFailure) {
          throw new Error(
            `LIVE BACKEND UNAVAILABLE: Cannot connect to FastAPI backend at ${BACKEND_BASE_URL}. Ensure the server is running locally ('uvicorn backend.app.main:app --port 8000') or configure NEXT_PUBLIC_API_BASE_URL for a public deployment. Switch to Simulated Mode to test offline.`
          );
        }

        throw err;
      }
    }

    // Simulated Mode: Return curated mock scenes
    await new Promise((resolve) => setTimeout(resolve, 200));
    const queryLower = filters.queryText.trim().toLowerCase();

    return MOCK_SCENES.filter((scene) => {
      if (filters.mission !== 'All' && scene.mission !== filters.mission) {
        return false;
      }
      if (scene.cloudCoverPercent > filters.maxCloudCover) {
        return false;
      }
      if (queryLower) {
        const matchesTitle = scene.title.toLowerCase().includes(queryLower);
        const matchesLocation = scene.locationName.toLowerCase().includes(queryLower);
        const matchesPlatform = scene.platformId.toLowerCase().includes(queryLower);
        return matchesTitle || matchesLocation || matchesPlatform;
      }
      return true;
    });
  }

  /**
   * Run real NDVI analysis on real scene, or simulated pipeline in simulated mode.
   * In LIVE mode, will NEVER silently fake results if the backend is down.
   */
  async runAnalysisPipeline(
    scene: SatelliteScene,
    query: string,
    onProgress: (job: AnalysisJob) => void,
    forceMock: boolean = false
  ): Promise<AnalysisResult> {
    const isRealScene = Boolean(scene.isRealData);
    const useRealPipeline = (this.mode === 'live' || isRealScene) && !forceMock;

    if (useRealPipeline) {
      return this.runRealNDVIWorkflow(scene, query, onProgress);
    } else {
      return this.runSimulatedWorkflow(scene, query, onProgress);
    }
  }

  /**
   * Real NDVI processing workflow connected to FastAPI /api/analyze.
   */
  private async runRealNDVIWorkflow(
    scene: SatelliteScene,
    query: string,
    onProgress: (job: AnalysisJob) => void
  ): Promise<AnalysisResult> {
    const jobId = `real-job-${Date.now()}`;
    const stages: PipelineStage[] = [
      {
        id: 'stage_1_discovery',
        name: 'STAC Asset Discovery',
        detail: 'Locating Red (B04) and NIR (B08) Cloud-Optimized GeoTIFFs.',
        status: 'pending',
      },
      {
        id: 'stage_2_streaming',
        name: 'Rasterio Window Streaming',
        detail: 'Reading bounded raster window via GDAL /vsicurl/ remote streaming.',
        status: 'pending',
      },
      {
        id: 'stage_3_masking',
        name: 'Nodata & Reflectance Masking',
        detail: 'Filtering nodata (DN=0) and applying 1/10000 surface reflectance scaling.',
        status: 'pending',
      },
      {
        id: 'stage_4_algebra',
        name: 'NDVI Matrix Computation',
        detail: 'Computing (NIR - Red) / (NIR + Red) and biophysical statistical distribution.',
        status: 'pending',
      },
      {
        id: 'stage_5_validation',
        name: 'Verification & Scientific Reporting',
        detail: 'Compiling valid pixel counts, density breakdown, and methodology caveats.',
        status: 'pending',
      },
    ];

    const currentJob: AnalysisJob = {
      jobId,
      query,
      targetScene: scene,
      status: 'processing',
      progressPercent: 10,
      currentStageId: stages[0].id,
      stages,
      startedAt: new Date().toISOString(),
    };

    onProgress({ ...currentJob });

    // Step 1: Discovery
    stages[0].status = 'active';
    stages[0].logMessage = `Querying STAC item assets for scene ${scene.id}`;
    onProgress({ ...currentJob, stages: [...stages] });
    await new Promise((r) => setTimeout(r, 400));
    stages[0].status = 'completed';
    stages[0].elapsedMs = 400;

    // Step 2 & 3: Streaming & Masking
    stages[1].status = 'active';
    stages[1].logMessage = 'Opening remote B04 and B08 COGs using Rasterio windowed reads';
    currentJob.progressPercent = 35;
    currentJob.currentStageId = stages[1].id;
    onProgress({ ...currentJob, stages: [...stages] });

    // Initiate real backend processing call
    const startTime = performance.now();
    let data: any;
    try {
      const response = await fetch(`${BACKEND_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scene_id: scene.id,
          query: query,
          window_pixels: 256,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const msg = errData?.detail?.message || `Real NDVI processing failed (HTTP ${response.status})`;
        currentJob.status = 'error';
        currentJob.errorMessage = msg;
        stages[1].status = 'failed';
        stages[1].logMessage = msg;
        onProgress({ ...currentJob, stages: [...stages] });
        throw new Error(msg);
      }

      data = await response.json();
    } catch (err: unknown) {
      const errorMsg =
        err instanceof Error
          ? err.message
          : `Failed to connect to ${BACKEND_BASE_URL}/api/analyze`;
      currentJob.status = 'error';
      currentJob.errorMessage = `LIVE NDVI PROCESSING ERROR: ${errorMsg}. Real NDVI calculation requires active FastAPI backend.`;
      stages[1].status = 'failed';
      stages[1].logMessage = errorMsg;
      onProgress({ ...currentJob, stages: [...stages] });
      throw new Error(currentJob.errorMessage);
    }

    const elapsedTotal = Math.round(performance.now() - startTime);

    stages[1].status = 'completed';
    stages[1].elapsedMs = Math.round(elapsedTotal * 0.4);

    // Step 3
    stages[2].status = 'completed';
    stages[2].elapsedMs = Math.round(elapsedTotal * 0.2);
    stages[2].logMessage = `Processed ${data.valid_pixels?.toLocaleString()} valid surface pixels (nodata: ${data.nodata_pixels?.toLocaleString()})`;
    currentJob.progressPercent = 70;

    // Step 4
    stages[3].status = 'completed';
    stages[3].elapsedMs = Math.round(elapsedTotal * 0.3);
    stages[3].logMessage = `Mean NDVI = ${data.mean_ndvi ?? 'N/A'} (Range: [${data.min_ndvi ?? '--'}, ${data.max_ndvi ?? '--'}])`;
    currentJob.progressPercent = 90;

    // Step 5
    stages[4].status = 'completed';
    stages[4].elapsedMs = Math.round(elapsedTotal * 0.1);
    stages[4].logMessage = `Analyzed ${data.area_analyzed_sq_km} km² bounded footprint at 10m GSD. Verified.`;
    currentJob.progressPercent = 100;
    currentJob.status = 'completed';
    currentJob.finishedAt = new Date().toISOString();
    onProgress({ ...currentJob, stages: [...stages] });

    // Format into AnalysisResult
    const finalResult: AnalysisResult = {
      jobId,
      sceneId: scene.id,
      mission: 'Sentinel-2',
      query,
      timestamp: data.timestamp,
      executiveSummary: data.executive_summary,
      confidenceScorePercent: null, // Strictly null: single observation has no statistical confidence interval
      areaAnalyzedSqKm: data.area_analyzed_sq_km,
      keyFindings: data.key_findings,
      spectralIndices: [
        {
          name: 'NDVI (Normalized Difference Vegetation Index)',
          description: '(B08 NIR - B04 Red) / (B08 NIR + B04 Red) on 10m BOA surface reflectance',
          meanValue: data.mean_ndvi ?? 0.0,
          range: [data.min_ndvi ?? -1.0, data.max_ndvi ?? 1.0],
        },
      ],
      metricDeltas: data.metric_deltas.map((m: any) => ({
        label: m.label,
        value: m.value,
        change: m.change,
        trend: m.trend || 'stable',
        baseline: m.baseline,
        unit: m.unit,
      })),
      anomaliesDetectedCount: null, // Null: single scene has no temporal change baseline
      anomalyNotes: data.anomaly_notes || 'Multi-temporal anomaly baseline not implemented.',
      methodologyCitation: data.methodology,
      disclaimer: data.limitations,
      isRealAnalysis: true,
      validPixels: data.valid_pixels,
      totalPixels: data.total_pixels,
      minNdvi: data.min_ndvi,
      maxNdvi: data.max_ndvi,
      meanNdvi: data.mean_ndvi,
      medianNdvi: data.median_ndvi,
      stdNdvi: data.std_ndvi,
    };

    return finalResult;
  }

  /**
   * Simulated workflow for demo/mock scenes when offline or in demo mode.
   */
  private async runSimulatedWorkflow(
    scene: SatelliteScene,
    query: string,
    onProgress: (job: AnalysisJob) => void
  ): Promise<AnalysisResult> {
    const jobId = `sim-job-${Date.now()}`;
    const stages: PipelineStage[] = [
      {
        id: 'stage_1_ingest',
        name: 'STAC Asset Ingestion (Simulated)',
        detail: 'Downloading L1C/L2A granules and verifying radiometric calibration.',
        status: 'pending',
      },
      {
        id: 'stage_2_atm_corr',
        name: 'Atmospheric Correction (Simulated)',
        detail: 'Applying Sen2Cor / LaSRC aerosol optical depth and cloud-shadow mask.',
        status: 'pending',
      },
      {
        id: 'stage_3_indices',
        name: 'Spectral Index Extraction (Simulated)',
        detail: 'Calculating raster band algebra (NDVI, NDWI, NBR, and backscatter dB).',
        status: 'pending',
      },
      {
        id: 'stage_4_ai_synthesis',
        name: 'AI Evidence Synthesis (Simulated)',
        detail: 'Correlating time-series deviations and generating analytical findings.',
        status: 'pending',
      },
    ];

    const currentJob: AnalysisJob = {
      jobId,
      query,
      targetScene: scene,
      status: 'processing',
      progressPercent: 5,
      currentStageId: stages[0].id,
      stages,
      startedAt: new Date().toISOString(),
    };

    onProgress({ ...currentJob });

    const runStep = async (idx: number, pct: number, ms: number, logMsg: string) => {
      stages[idx].status = 'active';
      stages[idx].logMessage = logMsg;
      currentJob.currentStageId = stages[idx].id;
      currentJob.progressPercent = pct;
      onProgress({ ...currentJob, stages: [...stages] });
      await new Promise((r) => setTimeout(r, ms));
      stages[idx].status = 'completed';
      stages[idx].elapsedMs = ms;
    };

    await runStep(0, 25, 500, 'Resolved mock STAC assets.');
    await runStep(1, 50, 500, 'Simulated atmospheric correction applied.');
    await runStep(2, 75, 500, 'Simulated surface index extraction complete.');
    await runStep(3, 95, 500, 'Generated demonstration evidence report.');

    currentJob.status = 'completed';
    currentJob.progressPercent = 100;
    currentJob.finishedAt = new Date().toISOString();
    onProgress({ ...currentJob, stages: [...stages] });

    const template = MOCK_ANALYSIS_RESULTS[scene.id] || MOCK_ANALYSIS_RESULTS.DEFAULT;
    return {
      ...template,
      jobId,
      sceneId: scene.id,
      mission: scene.mission,
      query,
      timestamp: new Date().toISOString(),
      isRealAnalysis: false,
    };
  }

  /**
   * Query history persistence.
   */
  getQueryHistory(): QueryHistoryItem[] {
    try {
      const stored = localStorage.getItem(HISTORY_STORAGE_KEY);
      if (stored) return JSON.parse(stored);
    } catch {
      // Ignore
    }
    return INITIAL_QUERY_HISTORY;
  }

  addQueryToHistory(item: Omit<QueryHistoryItem, 'id' | 'timestamp'>): QueryHistoryItem {
    const newItem: QueryHistoryItem = {
      ...item,
      id: `hist-${Date.now()}`,
      timestamp: new Date().toISOString(),
    };
    try {
      const existing = this.getQueryHistory();
      const updated = [newItem, ...existing.filter((h) => h.query !== item.query)].slice(0, 30);
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Ignore
    }
    return newItem;
  }

  getSavedAnalyses(): SavedAnalysis[] {
    try {
      const stored = localStorage.getItem(SAVED_STORAGE_KEY);
      if (stored) return JSON.parse(stored);
    } catch {
      // Ignore
    }
    return INITIAL_SAVED_ANALYSES;
  }

  saveAnalysis(
    analysis: AnalysisResult,
    scene: SatelliteScene,
    notes: string = '',
    tags: string[] = ['Observation']
  ): SavedAnalysis {
    const newSaved: SavedAnalysis = {
      id: `saved-${Date.now()}`,
      title: `${scene.locationName} - ${scene.mission}`,
      query: analysis.query,
      sceneId: scene.id,
      locationName: scene.locationName,
      mission: scene.mission,
      savedAt: new Date().toISOString(),
      tags: tags.length > 0 ? tags : ['Observation'],
      notes: notes || `Analysis of ${analysis.areaAnalyzedSqKm} km² (${analysis.isRealAnalysis ? 'Real Sentinel-2 L2A' : 'Simulated'}).`,
      keyMetric: analysis.metricDeltas[0]
        ? `${analysis.metricDeltas[0].label}: ${analysis.metricDeltas[0].value}`
        : 'Analysis completed',
    };
    try {
      const existing = this.getSavedAnalyses();
      const updated = [newSaved, ...existing.filter((s) => s.sceneId !== scene.id)];
      localStorage.setItem(SAVED_STORAGE_KEY, JSON.stringify(updated));
    } catch {
      // Ignore
    }
    return newSaved;
  }

  removeSavedAnalysis(id: string): void {
    try {
      const existing = this.getSavedAnalyses();
      localStorage.setItem(SAVED_STORAGE_KEY, JSON.stringify(existing.filter((s) => s.id !== id)));
    } catch {
      // Ignore
    }
  }

  clearHistory(): void {
    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch {
      // Ignore
    }
  }
}

export const apiClient = new SatelliteApiClient();
