import { useEffect, useState } from 'react';
import './app.module.css';

interface User {
  id: string;
  username: string;
  system_role: string;
}

interface Application {
  id: string;
  display_name: string;
  owner_id: string;
  root_node_id: string;
}

interface Node {
  id: string;
  application_id: string;
  path: string;
  container: Record<string, unknown>;
  metadata_: Record<string, unknown>;
}

export function App() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [app, setApp] = useState<Application | null>(null);
  const [node, setNode] = useState<Node | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Login and fetch data
    async function init() {
      try {
        // Step 1: Login as Sam
        const loginRes = await fetch('http://localhost:8000/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'Sam', password: 'Sam' }),
        });

        if (!loginRes.ok) throw new Error('Login failed');

        const loginData = await loginRes.json();
        setToken(loginData.access_token);
        setUser(loginData.user);

        // Step 2: Fetch applications
        const appsRes = await fetch('http://localhost:8000/api/v1/apps/', {
          headers: { Authorization: `Bearer ${loginData.access_token}` },
        });

        if (!appsRes.ok) throw new Error('Failed to fetch apps');

        const apps: Application[] = await appsRes.json();
        const ffs6App = apps.find((a) => a.display_name === 'Application 1XZ');
        if (!ffs6App) throw new Error('Application 1XZ not found');

        setApp(ffs6App);

        // Step 3: Fetch root node
        const nodeRes = await fetch(
          `http://localhost:8000/api/v1/apps/${ffs6App.id}/nodes/${ffs6App.root_node_id}`,
          {
            headers: { Authorization: `Bearer ${loginData.access_token}` },
          }
        );

        if (!nodeRes.ok) throw new Error('Failed to fetch node');

        const nodeData: Node = await nodeRes.json();
        setNode(nodeData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    }

    init();
  }, []);

  if (error) {
    return (
      <div style={{ padding: '20px', fontFamily: 'monospace' }}>
        <h1>❌ Error</h1>
        <p style={{ color: 'red' }}>{error}</p>
      </div>
    );
  }

  if (!user || !app || !node) {
    return (
      <div style={{ padding: '20px', fontFamily: 'monospace' }}>
        <h1>⏳ Loading...</h1>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>FFS6 - Application 1XZ</h1>

      <section style={{ marginTop: '20px' }}>
        <h2>👤 Logged in as</h2>
        <pre style={{ background: '#f4f4f4', padding: '10px', borderRadius: '4px' }}>
          {JSON.stringify(user, null, 2)}
        </pre>
      </section>

      <section style={{ marginTop: '20px' }}>
        <h2>📦 Application</h2>
        <pre style={{ background: '#f4f4f4', padding: '10px', borderRadius: '4px' }}>
          {JSON.stringify(app, null, 2)}
        </pre>
      </section>

      <section style={{ marginTop: '20px' }}>
        <h2>🌳 Root Node</h2>
        <pre style={{ background: '#f4f4f4', padding: '10px', borderRadius: '4px' }}>
          {JSON.stringify(node, null, 2)}
        </pre>
      </section>
    </div>
  );
}

export default App;
