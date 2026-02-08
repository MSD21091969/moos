# Codebase: FFS7 Collider Account Admin - ADMIN Domain

> Next.js admin dashboard with TanStack Table, React Hook Form, and comprehensive RBAC system

## Overview

The Collider Admin Dashboard is the central management interface for the Collider platform. It provides administrators with complete control over user accounts, permissions, billing, and system configuration. Built with Next.js App Router, it leverages modern React patterns and optimized data fetching for a responsive admin experience.

## Directory Structure

```
collider-frontend/apps/admin/
├── app/
│   ├── admin/
│   │   ├── layout.tsx                  # Admin layout with sidebar
│   │   ├── page.tsx                    # Dashboard home
│   │   ├── users/
│   │   │   ├── page.tsx                # User list
│   │   │   └── [id]/
│   │   │       └── page.tsx            # User detail/edit
│   │   ├── roles/
│   │   │   └── page.tsx                # Role management
│   │   ├── billing/
│   │   │   └── page.tsx                # Billing dashboard
│   │   ├── organizations/
│   │   │   └── page.tsx                # Org management
│   │   ├── api-keys/
│   │   │   └── page.tsx                # API key management
│   │   ├── audit-logs/
│   │   │   └── page.tsx                # Audit log viewer
│   │   └── settings/
│   │       └── page.tsx                # System settings
├── components/
│   ├── UserManagement/
│   │   ├── UserTable.tsx               # Data table
│   │   ├── UserForm.tsx                # Create/edit form
│   │   ├── UserInviteDialog.tsx        # Invite modal
│   │   └── UserFilters.tsx             # Search and filters
│   ├── RoleEditor/
│   │   ├── RoleForm.tsx                # Role creation
│   │   ├── PermissionMatrix.tsx        # Visual permission editor
│   │   └── RoleAssignment.tsx          # Assign users to roles
│   ├── BillingDashboard/
│   │   ├── SubscriptionList.tsx        # Active subscriptions
│   │   ├── InvoiceTable.tsx            # Invoice history
│   │   ├── UsageCharts.tsx             # Usage visualization
│   │   └── PaymentMethodForm.tsx       # Payment setup
│   ├── OrganizationManager/
│   │   ├── OrgTable.tsx                # Organizations list
│   │   ├── OrgForm.tsx                 # Create/edit org
│   │   └── OrgMembershipManager.tsx    # User-org relationships
│   ├── AuditLogViewer/
│   │   ├── AuditLogTable.tsx           # Log table
│   │   ├── AuditLogFilters.tsx         # Date/user/action filters
│   │   └── AuditLogDetail.tsx          # Detailed log view
│   ├── APIKeyManager/
│   │   ├── APIKeyTable.tsx             # API keys list
│   │   ├── APIKeyGenerator.tsx         # Generate new key
│   │   └── APIKeyRevoke.tsx            # Revoke key dialog
│   └── shared/
│       ├── AdminSidebar.tsx            # Admin navigation
│       ├── ProtectedRoute.tsx          # Permission guard
│       └── PermissionGate.tsx          # Conditional rendering
├── hooks/
│   ├── usePermissions.ts               # Permission checks
│   ├── useUsers.ts                     # User data management
│   ├── useRoles.ts                     #Role operations
│   ├── useBilling.ts                   # Billing data
│   └── useAuditLogs.ts                 # Audit log fetching
├── stores/
│   ├── adminStore.ts                   # Global admin state
│   ├── userStore.ts                    # User data cache
│   ├── roleStore.ts                    # Roles and permissions
│   ├── billingStore.ts                 # Billing state
│   └── auditLogStore.ts                # Audit logs
├── middleware/
│   └── adminAuth.ts                    # Admin route protection
└── types/
    ├── user.ts                         # User types
    ├── role.ts                         # Role/permission types
    ├── billing.ts                      # Billing types
    └── auditLog.ts                     # Audit log types
```

## Component Architecture

### Core Components

**UserTable** (`components/UserManagement/UserTable.tsx`)
- **Purpose**: Paginated, sortable, filterable user table
- **Props**:
  - `users: User[]` - User data
  - `pagination: PaginationState`
  - `onEdit: (user: User) => void`
  - `onDelete: (userId: string) => void`
- **State**: Column visibility, filters, selection
- **Dependencies**: @tanstack/react-table
- **Integration**: Uses `useUsers` hook

**RoleEditor** (`components/RoleEditor/PermissionMatrix.tsx`)
- **Purpose**: Visual matrix for editing role permissions
- **Props**:
  - `role: Role`
  - `onChange: (permissions: Permission[]) => void`
- **State**: Permission selections
- **Dependencies**: React Hook Form, Zod
- **Integration**: POST /api/admin/roles + PUT /api/admin/roles/:id/permissions

**BillingDashboard** (`components/BillingDashboard`)
- **Purpose**: Subscription and usage overview
- **Props**: None (uses billing store)
- **State**: Chart data, selected plan
- **Dependencies**: Recharts, Stripe elements
- **Integration**: Stripe API via backend

## Data Flow

### User Management Flow

```
1. Admin navigates to /admin/users
2. UserTable component renders
3. useUsers hook → GET /api/admin/users
4. TanStack Query caches response
5. Table renders with data, pagination, sorting
6. Admin clicks "Edit" → Opens UserForm dialog
7. Form submission → PUT /api/admin/users/:id
8. Success → Invalidate query cache → Table refreshes
9. Log audit entry → POST /api/admin/audit-logs
```

### Permission Check Flow

```
1. Component needs permission check
2. usePermissions hook → reads user.roles
3. Checks if role has required permission
4. Returns boolean
5. Component conditionally renders/enables features
6. Backend also validates permissions on API calls
```

### Billing Update Flow

```
1. Admin updates subscription plan
2. BillingDashboard → POST /api/admin/billing/subscriptions
3. Backend creates Stripe subscription
4. Webhook confirms → Updates database
5. Frontend polls or receives WebSocket update
6. UI reflects new subscription status
```

## Key Features Implementation

### Feature 1: User Management

**Implementation:**
```typescript
// hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@collider/api-client';

export function useUsers() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => apiClient.admin.users.list(),
  });

  const createUser = useMutation({
    mutationFn: (user: CreateUserDto) => apiClient.admin.users.create(user),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  const updateUser = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserDto }) =>
      apiClient.admin.users.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  const deleteUser = useMutation({
    mutationFn: (id: string) => apiClient.admin.users.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
    },
  });

  return {
    users: data?.users || [],
    isLoading,
    createUser,
    updateUser,
    deleteUser,
  };
}
```

### Feature 2: RBAC System

**Implementation:**
```typescript
// hooks/usePermissions.ts
import { useAuth } from '@/hooks/useAuth';

export function usePermissions() {
  const { user } = useAuth();

  const can = (resource: string, action: string): boolean => {
    if (!user) return false;

    return user.roles.some((role) =>
      role.permissions.some(
        (permission) =>
          permission.resource === resource &&
          permission.actions.includes(action)
      )
    );
  };

  const hasRole = (roleName: string): boolean => {
    return user?.roles.some((role) => role.name === roleName) ?? false;
  };

  return { can, hasRole };
}

// components/shared/PermissionGate.tsx
export function PermissionGate({
  resource,
  action,
  children,
  fallback = null,
}: PermissionGateProps) {
  const { can } = usePermissions();

  if (!can(resource, action)) {
    return fallback;
  }

  return <>{children}</>;
}

// Usage
<PermissionGate resource="users" action="delete">
  <Button onClick={handleDelete}>Delete</Button>
</PermissionGate>
```

### Feature 3: Audit Logging

**Implementation:**
```typescript
// components/AuditLogViewer/AuditLogTable.tsx
export function AuditLogTable() {
  const { logs, isLoading, filters, setFilters } = useAuditLogs();

  const columns = useMemo(() => [
    {
      accessorKey: 'timestamp',
      header: 'Time',
      cell: ({ getValue }) => formatDate(getValue()),
    },
    {
      accessorKey: 'userName',
      header: 'User',
    },
    {
      accessorKey: 'action',
      header: 'Action',
      cell: ({ getValue }) => <Badge>{getValue()}</Badge>,
    },
    {
      accessorKey: 'resource',
      header: 'Resource',
    },
    {
      accessorKey: 'changes',
      header: 'Details',
      cell: ({ getValue }) => (
        <AuditLogDetail changes={getValue()} />
      ),
    },
  ], []);

  const table = useReactTable({
    data: logs,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div>
      <AuditLogFilters filters={filters} onChange={setFilters} />
      <Table>
        {/* Render table */}
      </Table>
    </div>
  );
}
```

## Styling Approach

- **Framework**: Tailwind CSS
- **Components**: Shadcn/ui components
- **Layout**: Sidebar + main content area
- **Theme**: Admin-specific dark theme

## Performance Considerations

- **TanStack Query**: Aggressive caching, stale-while-revalidate
- **Table Virtualization**: For large user lists (react-window)
- **Lazy Loading**: Code split admin routes
- **Optimistic Updates**: UI updates before API confirms

## Testing

### Unit Tests
```bash
npx nx test admin
```

### Test Strategy
- Component tests: Form validation, table rendering
- Hook tests: Permission logic, data fetching
- Integration tests: Full user flow (create → edit → delete)

## Security Best Practices

- Admin routes protected by middleware
- Permission checks on every action
- Audit all admin operations
- Rate limiting on sensitive endpoints
- Re-authentication for critical actions (user delete, etc.)

## Related Code

- **Backend API**: `FFS2_ColliderBackends/ColliderDataServer/`
- **Shared UI**: `libs/shared-ui/`
- **API Client**: `libs/api-client/`

## Development Workflow

1. **Adding new admin feature**:
   ```bash
   # Create page in app/admin/
   # Add components
   # Create hooks for data fetching
   # Add permission checks
   # Test with different roles
   ```

2. **Testing permissions**:
   - Use different test accounts with varying roles
   - Verify UI reflects permissions correctly
   - Test API returns correct access errors

3. **Building for production**:
   ```bash
   npx nx build admin
   ```