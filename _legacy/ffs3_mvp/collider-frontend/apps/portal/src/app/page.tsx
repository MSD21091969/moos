'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import styles from './page.module.css';
import { api } from './api';
import { useAuth } from './AuthContext';
import type { Application } from '@collider-frontend/api-client';

export default function Home() {
  const { user, loading: authLoading, token, isDevMode, signInWithGoogle, signOut } = useAuth();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Wait for auth to complete before fetching apps
    if (authLoading) return;

    // Skip if not authenticated and not in dev mode
    if (!token && !isDevMode) {
      setLoading(false);
      return;
    }

    async function fetchApps() {
      try {
        const data = await api.listApplications();
        setApps(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load apps');
      } finally {
        setLoading(false);
      }
    }
    fetchApps();
  }, [authLoading, token, isDevMode]);

  const getDomainColor = (domain?: string) => {
    switch (domain) {
      case 'FILESYST': return '#22c55e';
      case 'ADMIN': return '#f97316';
      case 'CLOUD':
      default: return '#3b82f6';
    }
  };

  return (
    <main className={styles.page}>
      <header className={styles.header}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1>Collider Portal</h1>
            <p>Your context-aware AI workspace</p>
          </div>
          <div>
            {authLoading ? (
              <span style={{ color: '#64748b' }}>Loading...</span>
            ) : user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{ color: '#94a3b8' }}>{user.email}</span>
                <button
                  onClick={signOut}
                  style={{
                    padding: '0.5rem 1rem',
                    background: 'rgba(255,255,255,0.1)',
                    border: '1px solid rgba(255,255,255,0.2)',
                    borderRadius: '6px',
                    color: '#fff',
                    cursor: 'pointer'
                  }}
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                onClick={signInWithGoogle}
                style={{
                  padding: '0.5rem 1rem',
                  background: '#3b82f6',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#fff',
                  cursor: 'pointer'
                }}
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </header>

      <section className={styles.content}>
        <h2>Applications</h2>

        {loading && <div className={styles.loading}>Loading applications...</div>}

        {error && <div className={styles.error}>Error: {error}</div>}

        {!loading && !error && apps.length === 0 && (
          <div className={styles.empty}>No applications found. Run seed.py to create test data.</div>
        )}

        <div className={styles.grid}>
          {apps.map((app) => (
            <Link key={app.app_id} href={`/apps/${app.app_id}`} className={styles.card}>
              <div
                className={styles.cardBadge}
                style={{ backgroundColor: getDomainColor(app.domain) }}
              >
                {app.domain || 'CLOUD'}
              </div>
              <h3>{app.display_name || app.app_id}</h3>
              <p className={styles.appId}>{app.app_id}</p>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
