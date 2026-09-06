export type SupportedMission =
  | 'Sentinel-2'
  | 'Landsat-8/9'
  | 'Sentinel-1-SAR'
  | 'PlanetScope';

export type SensorType = 'Multispectral' | 'Optical' | 'Synthetic Aperture Radar (SAR)';

export type MapLayerType =
  | 'true_color'
  | 'false_color_ir'
  | 'ndvi'
  | 'sar_amplitude'
  | 'thermal';

export interface SpectralBand {
  id: string;
  name: string;
  commonName: string;
  centralWavelengthMicrons: number;
  bandwidthMicrons: number;
  spatialResolutionMeters: number;
  description: string;
  domain: 'Visible' | 'Near-Infrared' | 'Red-Edge' | 'Shortwave-Infrared' | 'Thermal' | 'SAR-Microwave';
}

export interface SatelliteScene {
  id: string;
  title: string;
  mission: SupportedMission;
  sensor: SensorType;
  platformId: string;
  instrument: string;
  acquisitionDate: string; // ISO string e.g. "2024-06-18T10:45:12Z"
  cloudCoverPercent: number;
  spatialResolutionMeters: number;
  crs: string; // e.g. "EPSG:32631 (WGS 84 / UTM zone 31N)"
  sunElevationDeg: number;
  sunAzimuthDeg: number;
  processingLevel: string; // e.g. "Level-2A (Bottom of Atmosphere)"
  centerCoordinates: {
    lat: number;
    lon: number;
  };
  boundingBox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
  locationName: string;
  orbitPass: 'Ascending' | 'Descending';
  relativeOrbitNumber: number;
  bands: SpectralBand[];
  simulatedLayerColorMap: Record<MapLayerType, string>;
  thumbnailSvgType: 'urban_port' | 'rainforest' | 'agricultural' | 'bay_valley' | 'glacial_ice';
  stacSelfHref: string;
  dataSizeMb: number;
  isRealData?: boolean;
  previewUrl?: string | null;
}

export type PipelineStageStatus = 'pending' | 'active' | 'completed' | 'failed';

export interface PipelineStage {
  id: string;
  name: string;
  detail: string;
  status: PipelineStageStatus;
  elapsedMs?: number;
  logMessage?: string;
}

export type JobStatus = 'idle' | 'queued' | 'processing' | 'completed' | 'error';

export interface AnalysisJob {
  jobId: string;
  query: string;
  targetScene: SatelliteScene;
  status: JobStatus;
  progressPercent: number;
  currentStageId: string;
  stages: PipelineStage[];
  startedAt?: string;
  finishedAt?: string;
  errorMessage?: string;
}

export interface MetricDelta {
  label: string;
  value: string;
  change: string | null;
  trend: 'increase' | 'decrease' | 'stable';
  baseline: string;
  unit: string;
}

export interface AnalysisResult {
  jobId: string;
  sceneId: string;
  mission: SupportedMission;
  query: string;
  timestamp: string;
  executiveSummary: string;
  confidenceScorePercent: number | null; // null for real single observation
  areaAnalyzedSqKm: number;
  keyFindings: string[];
  spectralIndices: {
    name: string;
    description: string;
    meanValue: number;
    range: [number, number];
  }[];
  metricDeltas: MetricDelta[];
  anomaliesDetectedCount: number | null;
  anomalyNotes: string;
  methodologyCitation: string;
  disclaimer: string;
  isRealAnalysis?: boolean;
  validPixels?: number;
  totalPixels?: number;
  minNdvi?: number | null;
  maxNdvi?: number | null;
  meanNdvi?: number | null;
  medianNdvi?: number | null;
  stdNdvi?: number | null;
  warnings?: string | null;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  locationName: string;
  missionFilter?: SupportedMission | 'All';
  timestamp: string;
  resultCount: number;
}

export interface SavedAnalysis {
  id: string;
  title: string;
  query: string;
  sceneId: string;
  locationName: string;
  mission: SupportedMission;
  savedAt: string;
  tags: string[];
  notes: string;
  keyMetric: string;
}

export interface SearchFilterParams {
  queryText: string;
  mission: SupportedMission | 'All';
  maxCloudCover: number; // 0 - 100
  startDate?: string;
  endDate?: string;
  resolution?: 'all' | '10m' | '15m' | '30m';
}

export interface BackendHealth {
  status: 'connected' | 'simulated_fallback' | 'offline' | 'error';
  service: string;
  version?: string;
  activeMode?: string;
  capabilities?: string[];
  providers?: string[];
  latencyMs?: number;
  lastChecked: string;
  message: string;
}

export type ActiveNavTab = 'dashboard' | 'history' | 'saved' | 'settings';
