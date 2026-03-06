import {
  SurfaceShell,
  startSurfaceSync,
} from '@moos/shared-ui';
import { useEffect, useState } from 'react';

type ApiRecord = {
  URN?: string;
  urn?: string;
  Kind?: string;
  kind?: string;
  ParentURN?: { String?: string; Valid?: boolean } | null;
  parent_urn?: string | null;
};

type TreeNode = {
  urn: string;
  kind: string;
  children: TreeNode[];
};

const resolveApiBase = (): string => {
  const value = import.meta.env.VITE_DATA_SERVER_URL as string | undefined;
  const base = value && value.trim().length > 0 ? value : 'http://127.0.0.1:8000';
  return base.replace(/\/$/, '');
};

const resolveToken = (): string => {
  const value = import.meta.env.VITE_MOOS_BEARER_TOKEN as string | undefined;
  return value && value.trim().length > 0 ? value : 'dev-token';
};

const parseUrn = (record: ApiRecord): string => record.URN ?? record.urn ?? '';

const parseParentUrn = (record: ApiRecord): string | null => {
  if (record.parent_urn) {
    return record.parent_urn;
  }
  if (record.ParentURN?.Valid && record.ParentURN.String) {
    return record.ParentURN.String;
  }
  return null;
};

const parseKind = (record: ApiRecord): string => record.Kind ?? record.kind ?? 'data';

const buildTree = (records: ApiRecord[], rootUrn: string): TreeNode | null => {
  const map = new Map<string, TreeNode>();
  const parentByChild = new Map<string, string | null>();

  for (const record of records) {
    const urn = parseUrn(record);
    if (!urn) {
      continue;
    }
    map.set(urn, { urn, kind: parseKind(record), children: [] });
    parentByChild.set(urn, parseParentUrn(record));
  }

  for (const [urn, node] of map.entries()) {
    const parentUrn = parentByChild.get(urn);
    if (!parentUrn) {
      continue;
    }
    const parent = map.get(parentUrn);
    if (parent) {
      parent.children.push(node);
    }
  }

  return map.get(rootUrn) ?? null;
};

const labelFromUrn = (urn: string): string => {
  const parts = urn.split(':');
  return parts[parts.length - 1] || urn;
};

const Tree = ({ node }: { node: TreeNode }): JSX.Element => {
  return (
    <li>
      <span>{labelFromUrn(node.urn)} </span>
      <small style={{ color: '#6b7280' }}>({node.kind})</small>
      {node.children.length > 0 ? (
        <ul>
          {node.children
            .sort((left, right) => left.urn.localeCompare(right.urn))
            .map((child) => (
              <Tree key={child.urn} node={child} />
            ))}
        </ul>
      ) : null}
    </li>
  );
};

export function App() {
  const [viewerLink, setViewerLink] = useState('offline');
  const [viewerLinkAge, setViewerLinkAge] = useState('n/a');
  const [viewerLinkHealth, setViewerLinkHealth] = useState('stale');
  const [dataServerStatus, setDataServerStatus] = useState('unavailable');
  const [journeyProbe, setJourneyProbe] = useState('unavailable|unavailable|unavailable|unavailable');
  const [treeRoot, setTreeRoot] = useState<TreeNode | null>(null);
  const [treeStatus, setTreeStatus] = useState('loading');

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
        if (health.status === 'unavailable' && probe.health === 'ok') {
          return 'ok';
        }
        return health.status;
      },
      onApiStatus: (status) => {
        setDataServerStatus(status);
      },
    });
  }, []);

  useEffect(() => {
    const rootUrn = 'urn:moos:root';
    const url = `${resolveApiBase()}/api/v1/containers/${encodeURIComponent(rootUrn)}/tree`;
    const headers = { Authorization: `Bearer ${resolveToken()}` };

    const loadTree = async (): Promise<void> => {
      try {
        const response = await fetch(url, { headers });
        if (!response.ok) {
          setTreeStatus(`error:${response.status}`);
          return;
        }
        const payload = (await response.json()) as ApiRecord[];
        const nextTree = buildTree(payload, rootUrn);
        if (!nextTree) {
          setTreeStatus('empty');
          return;
        }
        setTreeRoot(nextTree);
        setTreeStatus('ok');
      } catch {
        setTreeStatus('error:network');
      }
    };

    void loadTree();
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
          { label: 'tree-status', value: treeStatus },
          { label: 'contract', value: 'moos.surface.v1' },
        ]}
      />
      <section style={{ padding: '0 20px 20px 20px' }}>
        <h2 style={{ fontSize: '14px', margin: '8px 0' }}>Workspace Tree</h2>
        {treeRoot ? (
          <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px' }}>
            <Tree node={treeRoot} />
          </ul>
        ) : (
          <p style={{ fontSize: '13px', color: '#6b7280', margin: 0 }}>
            Tree not available ({treeStatus})
          </p>
        )}
      </section>
    </div>
  );
}

export default App;
