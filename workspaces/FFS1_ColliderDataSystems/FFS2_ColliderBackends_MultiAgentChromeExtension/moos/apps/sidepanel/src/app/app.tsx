import {
  SurfaceShell,
  startSurfaceSync,
} from '@moos/shared-ui';
import { useEffect, useState } from 'react';

export function App() {
  const [viewerLink, setViewerLink] = useState('offline');
  const [viewerLinkAge, setViewerLinkAge] = useState('n/a');
  const [viewerLinkHealth, setViewerLinkHealth] = useState('stale');
  const [dataServerStatus, setDataServerStatus] = useState('unavailable');
  const [journeyProbe, setJourneyProbe] = useState('unavailable|unavailable|unavailable|unavailable');

  useEffect(() => {
    return startSurfaceSync({
      selfSurface: 'sidepanel',
      selfStatus: 'active',
      phase: 'phase-5-scaffold',
      peerSurface: 'viewer',
      apiBaseUrl: import.meta.env.VITE_DATA_SERVER_URL,
      staleThresholdValue: import.meta.env.VITE_SURFACE_STALE_THRESHOLD_SECONDS,
      onPeerDiagnostics: (diagnostics) => {
        setViewerLink(diagnostics.link);
        setViewerLinkAge(diagnostics.ageLabel);
        setViewerLinkHealth(diagnostics.health);
      },
      buildApiStatus: async (api) => {
        const probe = await api.getJourneyProbe(['bootstrap.morphism']);
        setJourneyProbe(`${probe.status}|${probe.health}|${probe.compose}|${probe.bootstrap}`);
        const health = await api.getDataServerHealth();
        return health.status;
      },
      onApiStatus: (status) => {
        setDataServerStatus(status);
      },
    });
  }, []);

  return (
    <div>
      <SurfaceShell
        product="sidepanel"
        title="MOOS Sidepanel"
        subtitle="Phase 5 product surface scaffold"
        details={[
          { label: 'viewer-link', value: viewerLink },
          { label: 'viewer-link-age', value: viewerLinkAge },
          { label: 'viewer-link-health', value: viewerLinkHealth },
          { label: 'data-server', value: dataServerStatus },
          { label: 'journey-probe', value: journeyProbe },
          { label: 'contract', value: 'moos.surface.v1' },
        ]}
      />
    </div>
  );
}

export default App;
