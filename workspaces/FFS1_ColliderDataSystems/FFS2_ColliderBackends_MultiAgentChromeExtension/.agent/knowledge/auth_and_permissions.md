# Auth & Permissions

> How authentication, system roles, app roles, and the access request flow work.

---

## Authentication

### DataServer Auth (Current)

- **Method**: Username/password + JWT
- **Login**: `POST /api/v1/auth/login` — returns `{ access_token, user }`
- **Signup**: `POST /api/v1/auth/signup` — creates user with default `app_user` role
- **JWT**: HS256, sent as `Authorization: Bearer <token>`
- **Password**: bcrypt hashed

### Chrome Extension Auth (Planned)

- **Method**: Firebase Google sign-in
- **Flow**: Firebase popup → ID token → exchange for DataServer JWT

---

## System Roles

Stored on `User.system_role`. Determines platform-level access.

| Role | Code | Can Do |
|------|------|--------|
| Superadmin (SAD) | `superadmin` | Everything. Assign any role. |
| Collider Admin (CAD) | `collider_admin` | Assign app_admin/app_user. Manage all apps. |
| App Admin | `app_admin` | Create apps. Grant app permissions. |
| App User | `app_user` | Basic authenticated access. Request app access. |

### Role Assignment

- **Endpoint**: `POST /api/v1/users/{user_id}/assign-role`
- **Who**: Only SAD and CAD (via `require_collider_admin` dependency)
- **Constraint**: CAD cannot assign `superadmin` or `collider_admin` roles

---

## App Roles

Stored on `AppPermission.role`. Determines per-application access.

| Role | Code | Meaning |
|------|------|---------|
| App Admin | `app_admin` | Owner/admin of the application |
| App User | `app_user` | Regular member of the application |

---

## Access Request Flow

### 1. User Requests Access

```
POST /api/v1/apps/{id}/request-access
Body: { "message": "I need access to..." }  (optional)

Creates AppAccessRequest with status="pending"
```

### 2. Admin Views Pending Requests

```
GET /api/v1/apps/{id}/pending-requests

Returns list of pending AppAccessRequest records
Requires: app owner (app_admin) or CAD+
```

### 3. Admin Approves or Rejects

```
POST /api/v1/apps/{id}/requests/{request_id}/approve
Body: { "role": "app_user" }

Creates AppPermission with the specified role
Sets request status="approved", resolved_at, resolved_by
```

```
POST /api/v1/apps/{id}/requests/{request_id}/reject

Sets request status="rejected", resolved_at, resolved_by
```

---

## Who Can Do What

| Action | SAD | CAD | App Admin | App User |
|--------|-----|-----|-----------|----------|
| Assign system roles | Any | app_admin, app_user only | No | No |
| Create applications | Yes | Yes | Yes | No |
| Approve/reject access | Yes | Yes | Own apps only | No |
| Request app access | Yes | Yes | Yes | Yes |
| Access app data | Yes | Yes | If permitted | If permitted |

---

_v1.0.0 — 2026-02-17_
