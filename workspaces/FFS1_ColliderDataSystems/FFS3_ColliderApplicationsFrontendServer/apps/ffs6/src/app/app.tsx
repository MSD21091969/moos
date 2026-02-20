import { useState, useEffect } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  useNavigate,
} from 'react-router-dom';
import { TreeView, getContextTheme } from '@collider/shared-ui';
import { AdminDashboard } from '../views/AdminDashboard';
import { RoleAssignment } from '../views/RoleAssignment';
import { PermissionGrant } from '../views/PermissionGrant';
import { NodeDetails } from '../views/NodeDetails';

function Layout() {
  const [nodes, setNodes] = useState<any[]>([]); // Array for TreeView
  const [app, setApp] = useState<any>(null);
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    // Login and fetch initial data
    const init = async () => {
      try {
        // 1. Login (mock)
        const loginRes = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'Sam', password: 'Sam' }),
        });
        if (!loginRes.ok) throw new Error('Login failed');
        const loginData = await loginRes.json();
        // Store token
        if (loginData && loginData.access_token) {
          localStorage.setItem('auth_token', loginData.access_token);
        }

        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (loginData && loginData.access_token) {
          headers['Authorization'] = `Bearer ${loginData.access_token}`;
        }

        // 2. Get User
        const userRes = await fetch('/api/v1/users/me', { headers });
        setUser(await userRes.json());

        // 3. Get Apps
        const appsRes = await fetch('/api/v1/apps/', { headers });
        const apps = await appsRes.json();

        if (apps && apps.length > 0) {
          const firstApp = apps[0];
          setApp(firstApp);

          // 4. Get Node Tree for App
          const treeRes = await fetch(
            `/api/v1/apps/${firstApp.id}/nodes/tree`,
            { headers },
          );
          setNodes(await treeRes.json());
        }

        setLoading(false);
      } catch (err) {
        console.error('Init failed', err);
        setLoading(false);
      }
    };
    init();
  }, []);

  if (loading) return <div style={{ padding: '20px' }}>Loading FFS6...</div>;

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      {/* Sidebar */}
      <div
        style={{
          width: '280px',
          borderRight: '1px solid #e5e7eb',
          padding: '16px',
          backgroundColor: '#f9fafb',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <div
          style={{ marginBottom: '20px', fontWeight: 'bold', fontSize: '18px' }}
        >
          FFS6 Viewer
        </div>

        {app && (
          <div
            style={{ marginBottom: '10px', fontSize: '12px', color: '#6b7280' }}
          >
            App: <strong>{app.display_name}</strong>
          </div>
        )}

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <div
            style={{
              marginBottom: '16px',
              fontWeight: 600,
              color: '#6b7280',
              fontSize: '12px',
              textTransform: 'uppercase',
            }}
          >
            Explorer
          </div>
          {nodes.map((node) => (
            <TreeView
              key={node.id}
              node={node}
              onSelect={(n) => navigate(`/nodes/${n.id}`)}
            />
          ))}
        </div>

        <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
          <div
            style={{
              marginBottom: '8px',
              fontWeight: 600,
              color: '#6b7280',
              fontSize: '12px',
              textTransform: 'uppercase',
            }}
          >
            System
          </div>
          <Link
            to="/admin"
            style={{
              display: 'block',
              padding: '8px',
              textDecoration: 'none',
              color: '#374151',
              borderRadius: '4px',
              marginBottom: '4px',
            }}
            onMouseEnter={(e) =>
              (e.currentTarget.style.backgroundColor = '#f3f4f6')
            }
            onMouseLeave={(e) =>
              (e.currentTarget.style.backgroundColor = 'transparent')
            }
          >
            ⚙️ Administration
          </Link>
          {user && (
            <div
              style={{ marginTop: '12px', fontSize: '12px', color: '#6b7280' }}
            >
              Logged in as: {user.username}
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, overflowY: 'auto', backgroundColor: '#ffffff' }}>
        <Routes>
          <Route
            path="/"
            element={
              <div
                style={{
                  padding: '40px',
                  textAlign: 'center',
                  color: '#6b7280',
                }}
              >
                <h1>Welcome to FFS6</h1>
                <p>Select a node from the explorer to view details.</p>
              </div>
            }
          />
          <Route
            path="/admin"
            element={<AdminDashboard onNavigate={navigate} />}
          />
          <Route
            path="/admin/assign-roles"
            element={<RoleAssignment onBack={() => navigate('/admin')} />}
          />
          <Route
            path="/admin/grant-permission"
            element={<PermissionGrant onBack={() => navigate('/admin')} />}
          />
          <Route
            path="/nodes/:id"
            element={
              app ? <NodeDetails appId={app.id} /> : <div>Select App</div>
            }
          />
        </Routes>
      </div>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  );
}
