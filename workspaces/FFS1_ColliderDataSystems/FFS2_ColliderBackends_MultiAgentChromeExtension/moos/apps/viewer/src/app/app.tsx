import {
  SurfaceShell,
  startSurfaceSync,
} from '@moos/shared-ui';
import { useEffect, useState } from 'react';

export function App() {
  const [sidepanelLink, setSidepanelLink] = useState('offline');
  const [sidepanelLinkAge, setSidepanelLinkAge] = useState('n/a');
  const [sidepanelLinkHealth, setSidepanelLinkHealth] = useState('stale');
  const [bootstrapStatus, setBootstrapStatus] = useState('unavailable:0');
  const [journeyProbe, setJourneyProbe] = useState('unavailable|unavailable|unavailable|unavailable');

  useEffect(() => {
    return startSurfaceSync({
      selfSurface: 'viewer',
      selfStatus: 'ready',
      phase: 'phase-5-scaffold',
      peerSurface: 'sidepanel',
      apiBaseUrl: import.meta.env.VITE_DATA_SERVER_URL,
      staleThresholdValue: import.meta.env.VITE_SURFACE_STALE_THRESHOLD_SECONDS,
      onPeerDiagnostics: (diagnostics) => {
        setSidepanelLink(diagnostics.link);
        setSidepanelLinkAge(diagnostics.ageLabel);
        setSidepanelLinkHealth(diagnostics.health);
      },
      buildApiStatus: async (api) => {
        const probe = await api.getJourneyProbe(['bootstrap.morphism']);
        setJourneyProbe(`${probe.status}|${probe.health}|${probe.compose}|${probe.bootstrap}`);
        const preview = await api.getBootstrapPreview(['bootstrap.morphism']);
        return `${preview.status}:${preview.messageCount}`;
      },
      onApiStatus: (status) => {
        setBootstrapStatus(status);
      },
    });
  }, []);

  return (
    <div>
      <SurfaceShell
        product="viewer"
        title="MOOS Viewer"
        subtitle="Phase 5 product surface scaffold"
        details={[
          { label: 'sidepanel-link', value: sidepanelLink },
          { label: 'sidepanel-link-age', value: sidepanelLinkAge },
          { label: 'sidepanel-link-health', value: sidepanelLinkHealth },
          { label: 'bootstrap-preview', value: bootstrapStatus },
          { label: 'journey-probe', value: journeyProbe },
          { label: 'contract', value: 'moos.surface.v1' },
        ]}
      />
    </div>
  );
}

export default App;
