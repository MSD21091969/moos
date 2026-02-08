# FFS7 Collider Account Admin - ADMIN Domain - Agent Context

> Admin dashboard for user account and permission management in the Collider system

## Location

`D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS3_ColliderApplicationsFrontendServer\FFS7_applicationz_ADMIN_ColliderAccount_appnodes\.agent\`

## Hierarchy

```
FFS0_Factory (Root)
  └── FFS1_ColliderDataSystems (IDE Context)
        └── FFS3_ColliderFrontend (Frontend Server)
              └── FFS7_Admin (This Application)
```

## Purpose

### User-Facing Purpose
The Admin Dashboard provides comprehensive account and system management:
- User account creation and management
- Permission and role assignment
- Billing and subscription management
- System settings and configuration
- Audit logs and activity monitoring
- API key management
- Organization and team management

### Technical Role
Acts as the central administrative interface for the Collider platform:
- CRUD operations for users, roles, permissions
- Integration with authentication/authorization system
- Billing system integration (Stripe/similar)
- Real-time activity monitoring
- Audit trail tracking
- Multi-tenant organization management

### Key Responsibilities
- Manage user accounts across the platform
- Configure roles and permissions (RBAC)
- Handle billing and subscription plans
- Monitor system usage and quotas
- Generate reports and analytics
- Manage API keys and OAuth applications
- Configure system-wide settings

## Key Components

### Pages/Routes
- `/admin` - Admin dashboard home
- `/admin/users` - User management
- `/admin/users/:id` - User detail/edit
- `/admin/roles` - Role and permission management
- `/admin/billing` - Billing and subscriptions
- `/admin/organizations` - Organization management
- `/admin/api-keys` - API key management
- `/admin/audit-logs` - Activity audit trail
- `/admin/settings` - System configuration

### Main Components
- **UserManagement** (`src/components/UserManagement.tsx`) - Users table with CRUD actions
- **RoleEditor** (`src/components/RoleEditor.tsx`) - Role and permission assignment
- **BillingDashboard** (`src/components/BillingDashboard.tsx`) - Subscription and payment management
- **OrganizationManager** (`src/components/OrganizationManager.tsx`) - Multi-tenant org management
- **AuditLogViewer** (`src/components/AuditLogViewer.tsx`) - Activity log browser
- **APIKeyManager** (`src/components/APIKeyManager.tsx`) - API key generation and revocation
- **UserInviteDialog** (`src/components/UserInviteDialog.tsx`) - Invite new users
- **PermissionMatrix** (`src/components/PermissionMatrix.tsx`) - Visual permission editor

### State Management
- **Zustand stores** for admin state
- Key stores:
  - `useAdminStore` - Admin UI state, filters, selections
  - `useUserStore` - User data, pagination
  - `useRoleStore` - Roles and permissions
  - `useBillingStore` - Subscription plans, invoices
  - `useAuditLogStore` - Audit trail data

### Integration Points

**Backend APIs:**
- `GET /api/admin/users` - List users with pagination
- `POST /api/admin/users` - Create user
- `PUT /api/admin/users/:id` - Update user
- `DELETE /api/admin/users/:id` - Deactivate user
- `GET /api/admin/roles` - List roles
- `POST /api/admin/roles` - Create role
- `PUT /api/admin/roles/:id/permissions` - Update role permissions
- `GET /api/admin/billing/subscriptions` - List subscriptions
- `POST /api/admin/billing/subscriptions` - Create subscription
- `GET /api/admin/audit-logs` - Fetch audit logs
- `POST /api/admin/api-keys` - Generate API key
- `DELETE /api/admin/api-keys/:id` - Revoke API key

**Authentication:**
- Requires admin-level permissions
- Role-based access control (RBAC)
- Protected routes with admin guards

**Other FFS Apps:**
- FFS8 (my-tiny-data-collider): User's data quota management
- FFS4 (Sidepanel): Admin context switching

## Development

### Running Locally

```bash
cd collider-frontend
pnpm dev
# Navigate to http://localhost:3000/admin
# Login with admin credentials
```

### Key Dependencies

- `@tanstack/react-table` - Data tables for users/logs
- `@tanstack/react-query` - Server state caching
- `recharts` - Billing and usage charts
- `react-hook-form` - Form handling
- `zod` - Form validation
- `@collider/api-client` - Backend API calls

### Environment Variables

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
NEXT_PUBLIC_ADMIN_ROLES=super_admin,admin
```

## Role-Based Access Control (RBAC)

### Permission Model

```typescript
interface Permission {
  resource: string;  // e.g., "users", "roles", "billing"
  actions: string[]; // e.g., ["read", "create", "update", "delete"]
}

interface Role {
  id: string;
  name: string;
  description: string;
  permissions: Permission[];
}
```

### Standard Roles

- **Super Admin**: Full system access
- **Admin**: User and organization management
- **Billing Admin**: Billing and subscription management
- **Support**: Read-only access for support tasks
- **User Manager**: User CRUD operations only

### Permission Checks

```typescript
// hooks/usePermissions.ts
export function usePermissions() {
  const { user } = useAuth();

  const can = (resource: string, action: string): boolean => {
    return user.permissions.some(
      (p) => p.resource === resource && p.actions.includes(action)
    );
  };

  return { can };
}

// Usage
const { can } = usePermissions();
if (can('users', 'delete')) {
  // Show delete button
}
```

## Domain Context

- **Domain**: admin
- **App Type**: admin-panel
- **Features**:
  - account_mgmt - User account CRUD
  - permissions - Role and permission management
  - billing - Subscription and payment handling
  - audit_logs - Activity tracking
  - api_keys - API key management
  - organizations - Multi-tenant org management

## Security Considerations

- Admin routes protected by middleware
- All actions logged to audit trail
- Sensitive operations require re-authentication
- Permission checks on both frontend and backend
- API keys encrypted at rest
- No PII visible without proper permissions

## Data Tables & Pagination

Uses TanStack Table for performant data tables:
- Client-side sorting and filtering
- Server-side pagination for large datasets
- Column visibility controls
- Export to CSV functionality

## Audit Logging

All admin actions are logged:
```typescript
interface AuditLog {
  id: string;
  timestamp: Date;
  userId: string;
  userName: string;
  action: string; // "user.created", "role.updated"
  resource: string;
  resourceId: string;
  changes: Record<string, any>;
  ipAddress: string;
}
```

## Related Documentation

- FFS3 Frontend: `../knowledge/codebase.md`
- Backend API: `../../../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderDataServer/.agent/`
- Authentication: See backend auth documentation