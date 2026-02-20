import { Card, Button, getContextTheme } from '@collider/shared-ui';

export function AdminDashboard({ onNavigate }: { onNavigate: (path: string) => void }) {
  const theme = getContextTheme('ADMIN');

  return (
    <div style={{ padding: '20px' }}>
      <h1 style={{ color: theme.primary, borderBottom: `2px solid ${theme.border}`, paddingBottom: '10px' }}>
        Administration
      </h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
        <Card 
          title="System Roles" 
          context="ADMIN" 
          style={{ cursor: 'pointer' }}
          onClick={() => onNavigate('/admin/assign-roles')}
        >
          <p>Manage system-wide roles for users (Superadmin, Collider Admin, App Admin).</p>
          <Button context="ADMIN" style={{ marginTop: '10px' }}>Manage Roles</Button>
        </Card>

        <Card 
          title="Access Requests" 
          context="ADMIN"
          style={{ cursor: 'pointer' }}
          onClick={() => onNavigate('/admin/grant-permission')}
        >
          <p>Review pending access requests for applications.</p>
          <Button context="ADMIN" style={{ marginTop: '10px' }}>Review Requests</Button>
        </Card>
      </div>
    </div>
  );
}
