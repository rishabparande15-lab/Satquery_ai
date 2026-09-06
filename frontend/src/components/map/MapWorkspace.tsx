import React from 'react';
import { MapLayerType, SatelliteScene } from '../../types/satellite';
import { LiveScenePreview } from './LiveScenePreview';

interface MapWorkspaceProps {
  scene: SatelliteScene | null;
  activeLayer: MapLayerType;
  onChangeLayer: (layer: MapLayerType) => void;
  onTriggerAnalysis: () => void;
  isAnalyzing: boolean;
}

/** Displays the selected STAC item's real natural-color preview and scene coordinates. */
export const MapWorkspace: React.FC<MapWorkspaceProps> = (props) => <LiveScenePreview {...props} />;
