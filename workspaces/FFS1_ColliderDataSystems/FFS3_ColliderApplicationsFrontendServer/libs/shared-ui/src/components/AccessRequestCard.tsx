import { Button } from './Button';
import { Card } from './Card';
import { UserRoleBadge } from './UserRoleBadge';

export interface AccessRequest {
  id: string;
  user: {
    username: string;
    system_role: string;
  };
  application_id: string;
  message?: string;
  requested_at: string;
  status: string;
}

export interface AccessRequestCardProps {
  request: AccessRequest;
  onApprove: (id: string, role: string) => void;
  onReject: (id: string) => void;
}

export function AccessRequestCard({ request, onApprove, onReject }: AccessRequestCardProps) {
  const date = new Date(request.requested_at).toLocaleDateString();

  return (
    <Card style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600, fontSize: '16px' }}>{request.user.username}</span>
            <UserRoleBadge role={request.user.system_role} type="system" />
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Requested access on {date}
          </div>
          {request.message && (
            <div style={{ 
              backgroundColor: '#f9fafb', 
              padding: '8px', 
              borderRadius: '4px', 
              fontSize: '14px', 
              fontStyle: 'italic',
              marginBottom: '12px'
            }}>
              "{request.message}"
            </div>
          )}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <Button 
            variant="primary" 
            onClick={() => onApprove(request.id, 'app_user')}
            style={{ fontSize: '13px' }}
          >
            Approve (User)
          </Button>
          <Button 
            variant="secondary"
            onClick={() => onApprove(request.id, 'app_admin')} 
            style={{ fontSize: '13px' }}
          >
            Approve (Admin)
          </Button>
          <Button 
            variant="danger" 
            onClick={() => onReject(request.id)}
            style={{ fontSize: '13px' }}
          >
            Reject
          </Button>
        </div>
      </div>
    </Card>
  );
}
