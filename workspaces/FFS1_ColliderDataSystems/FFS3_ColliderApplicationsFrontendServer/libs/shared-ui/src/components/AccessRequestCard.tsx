import { Button } from './Button';
import { Card } from './Card';
import { UserRoleBadge } from './UserRoleBadge';
import styles from './AccessRequestCard.module.css';

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
    <Card className={styles.card}>
      <div className={styles.layout}>
        <div>
          <div className={styles.headerRow}>
            <span className={styles.username}>{request.user.username}</span>
            <UserRoleBadge role={request.user.system_role} type="system" />
          </div>
          <div className={styles.subText}>
            Requested access on {date}
          </div>
          {request.message && (
            <div className={styles.message}>
              "{request.message}"
            </div>
          )}
        </div>

        <div className={styles.actions}>
          <Button
            variant="primary"
            onClick={() => onApprove(request.id, 'app_user')}
            className={styles.actionButton}
          >
            Approve (User)
          </Button>
          <Button
            variant="secondary"
            onClick={() => onApprove(request.id, 'app_admin')}
            className={styles.actionButton}
          >
            Approve (Admin)
          </Button>
          <Button
            variant="danger"
            onClick={() => onReject(request.id)}
            className={styles.actionButton}
          >
            Reject
          </Button>
        </div>
      </div>
    </Card>
  );
}
