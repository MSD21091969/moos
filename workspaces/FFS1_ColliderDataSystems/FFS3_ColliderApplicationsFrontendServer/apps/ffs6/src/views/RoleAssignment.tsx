import { useState, useEffect } from 'react';
import { Button, Card, getContextTheme } from '@collider/shared-ui';

interface User {
  id: string;
  username: string;
  email: string;
  system_role: string;
}

export function RoleAssignment({ onBack }: { onBack: () => void }) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>('');
  const [selectedRole, setSelectedRole] = useState<string>('app_user');
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const theme = getContextTheme('ADMIN');

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('auth_token');
        const res = await fetch('/api/v1/users', {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error('Failed to fetch users');
        const data = await res.json();
        if (Array.isArray(data)) {
          setUsers(data);
        } else {
          setUsers([]);
        }
      } catch (err) {
        console.error('Failed to load users', err);
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const handleAssign = async () => {
    if (!selectedUser) return;
    try {
      const token = localStorage.getItem('auth_token');
      const res = await fetch(`/api/v1/users/${selectedUser}/assign-role`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ system_role: selectedRole })
      });
      if (res.ok) {
        setMessage('Role assigned successfully!');
        // Refresh users list to show update
        try {
          const usersRes = await fetch('/api/v1/users', {
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
          });
          const updatedUsers = await usersRes.json();
          setUsers(Array.isArray(updatedUsers) ? updatedUsers : []);
        } catch {
          setUsers([]);
        }
      } else {
        const err = await res.json();
        setMessage(`Error: ${err.detail}`);
      }
    } catch (error) {
      setMessage('Failed to assign role');
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <Button onClick={onBack} variant="secondary" style={{ marginBottom: '20px' }} context="ADMIN">
        ← Back to Dashboard
      </Button>

      <Card title="Assign System Role" context="ADMIN">
        {loading ? (
          <p>Loading users...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Select User</label>
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #d1d5db'
                }}
              >
                <option value="">-- Select a User --</option>
                {Array.isArray(users) && users.length > 0 ? (
                  users.map(u => (
                    <option key={u.id} value={u.id}>
                      {u.username} ({u.system_role})
                    </option>
                  ))
                ) : (
                  <option disabled>No users found</option>
                )}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 500 }}>Select System Role</label>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #d1d5db'
                }}
              >
                <option value="app_user">App User</option>
                <option value="app_admin">App Admin</option>
                <option value="collider_admin">Collider Admin</option>
                <option value="superadmin">Superadmin</option>
              </select>
            </div>

            <Button
              onClick={handleAssign}
              disabled={!selectedUser}
              context="ADMIN"
              variant="primary"
            >
              Assign Role
            </Button>

            {message && (
              <div style={{
                padding: '10px',
                backgroundColor: message.startsWith('Error') ? '#fee2e2' : '#dcfce7',
                color: message.startsWith('Error') ? '#b91c1c' : '#15803d',
                borderRadius: '4px',
                marginTop: '10px'
              }}>
                {message}
              </div>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
