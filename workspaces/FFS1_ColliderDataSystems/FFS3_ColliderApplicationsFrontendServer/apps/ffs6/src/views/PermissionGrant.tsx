import { useState, useEffect } from 'react';
import { Button, AccessRequestCard, getContextTheme } from '@collider/shared-ui';

interface Application {
  id: string;
  name: string;
}

export function PermissionGrant({ onBack }: { onBack: () => void }) {
  const [apps, setApps] = useState<Application[]>([]);
  const [selectedApp, setSelectedApp] = useState<string>('');
  const [requests, setRequests] = useState<any[]>([]);
  const [loadingApps, setLoadingApps] = useState(true);
  const [loadingRequests, setLoadingRequests] = useState(false);
  const [message, setMessage] = useState('');

  const theme = getContextTheme('ADMIN');

  useEffect(() => {
    const fetchApps = async () => {
      setLoadingApps(true);
      try {
        const token = localStorage.getItem('auth_token');
        const res = await fetch('/api/v1/apps', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error('Failed to fetch apps');
        const data = await res.json();
        if (Array.isArray(data)) {
          setApps(data);
        } else {
          setApps([]);
        }
      } catch (err) {
        console.error('Failed to load apps', err);
        setApps([]);
      } finally {
        setLoadingApps(false);
      }
    };
    fetchApps();
  }, []);

  const loadRequests = async (appId: string) => {
    setLoadingRequests(true);
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`/api/v1/apps/${appId}/pending-requests`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error('Failed to fetch requests');
      const data = await res.json();
      setRequests(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load requests', err);
      setRequests([]);
    } finally {
      setLoadingRequests(false);
    }
  };

  useEffect(() => {
    if (selectedApp) {
      loadRequests(selectedApp);
    } else {
      setRequests([]);
    }
  }, [selectedApp]);

  const handleApprove = async (requestId: string, role: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`/api/v1/apps/${selectedApp}/requests/${requestId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ role })
      });
      if (res.ok) {
        setMessage('Request approved');
        loadRequests(selectedApp); // Reload
      } else {
        setMessage('Failed to approve');
      }
    } catch (e) {
      setMessage('Error approving request');
    }
  };

  const handleReject = async (requestId: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`/api/v1/apps/${selectedApp}/requests/${requestId}/reject`, {
        method: 'POST',
        headers: token ? { 'Authorization': `Bearer ${token}` } : {},
      });
      if (res.ok) {
        setMessage('Request rejected');
        loadRequests(selectedApp); // Reload
      } else {
        setMessage('Failed to reject');
      }
    } catch (e) {
      setMessage('Error rejecting request');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <Button onClick={onBack} variant="secondary" style={{ marginBottom: '20px' }} context="ADMIN">
        ← Back to Dashboard
      </Button>

      <h2 style={{ color: theme.primary, borderBottom: `1px solid ${theme.border}`, paddingBottom: '8px' }}>
        Grant Permissions
      </h2>

      {loadingApps ? (
        <p>Loading apps...</p>
      ) : (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Select Application</label>
          <select
            value={selectedApp}
            onChange={(e) => setSelectedApp(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #d1d5db'
            }}
          >
            <option value="">-- Select an Application --</option>
            {Array.isArray(apps) && apps.length > 0 ? (
              apps.map(app => (
                <option key={app.id} value={app.id}>{app.name}</option>
              ))
            ) : (
              <option disabled>No applications found</option>
            )}
          </select>
        </div>
      )}

      {selectedApp && (
        <div>
          <h3 style={{ marginBottom: '16px' }}>Pending Requests</h3>
          {loadingRequests ? (
            <p>Loading requests...</p>
          ) : requests.length === 0 ? (
            <p style={{ fontStyle: 'italic', color: '#6b7280' }}>No pending requests.</p>
          ) : (
            requests.map(req => (
              <AccessRequestCard
                key={req.id}
                request={req}
                onApprove={handleApprove}
                onReject={handleReject}
              />
            ))
          )}
        </div>
      )}

      {message && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          padding: '12px',
          backgroundColor: '#374151',
          color: 'white',
          borderRadius: '4px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.2)'
        }}>
          {message}
          <button
            onClick={() => setMessage('')}
            style={{ marginLeft: '10px', background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer' }}
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
}
