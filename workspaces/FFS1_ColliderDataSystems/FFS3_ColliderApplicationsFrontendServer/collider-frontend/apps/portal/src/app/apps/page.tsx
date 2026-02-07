'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '../api';
import type { Application } from '@collider-frontend/api-client';

export default function AppsPage() {
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listApplications()
      .then(setApps)
      .finally(() => setLoading(false));
  }, []);

  const groupedApps = apps.reduce((acc, app) => {
    const domain = app.domain || 'CLOUD';
    if (!acc[domain]) acc[domain] = [];
    acc[domain].push(app);
    return acc;
  }, {} as Record<string, Application[]>);

  return (
    <div style={{ padding: '2rem', background: '#1a1a2e', minHeight: '100vh', color: '#fff' }}>
      <h1 style={{ marginBottom: '2rem' }}>All Applications</h1>

      {loading ? (
        <p>Loading...</p>
      ) : (
        Object.entries(groupedApps).map(([domain, domainApps]) => (
          <section key={domain} style={{ marginBottom: '2rem' }}>
            <h2 style={{ color: domain === 'FILESYST' ? '#22c55e' : domain === 'ADMIN' ? '#f97316' : '#3b82f6' }}>
              {domain}
            </h2>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
              {domainApps.map(app => (
                <Link
                  key={app.app_id}
                  href={`/apps/${app.app_id}`}
                  style={{
                    padding: '1rem',
                    background: 'rgba(255,255,255,0.05)',
                    borderRadius: '8px',
                    color: '#fff',
                    textDecoration: 'none'
                  }}
                >
                  <strong>{app.display_name || app.app_id}</strong>
                  <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>{app.app_id}</p>
                </Link>
              ))}
            </div>
          </section>
        ))
      )}

      <Link href="/" style={{ color: '#3b82f6' }}>← Back to Portal</Link>
    </div>
  );
}
