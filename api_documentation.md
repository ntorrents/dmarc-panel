# DMARC Panel API Documentation

## Overview

This API provides secure authentication using HttpOnly cookies and comprehensive role-based access control for managing companies, users, domains, and DNS records.

## Authentication

### Login
```http
POST /api/v1/auth/auth/
Content-Type: application/json

{
    "action": "login",
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "message": "Login exitoso",
    "user": {
        "id": "uuid",
        "username": "username",
        "email": "user@example.com",
        "empresa_nombre": "Company Name",
        "role_nombre": "Company Admin",
        "permissions": {
            "is_super_admin": false,
            "is_company_admin": true,
            "can_edit_config": true,
            "is_read_only": false
        }
    }
}
```

### Logout
```http
POST /api/v1/auth/auth/
Content-Type: application/json

{
    "action": "logout"
}
```

### Refresh Token
```http
POST /api/v1/auth/auth/
Content-Type: application/json

{
    "action": "refresh"
}
```

### Get Profile
```http
GET /api/v1/auth/profile/
```

## User Roles

1. **Super Admin**: Full system access, can manage all companies and users
2. **Company Admin**: Full access within their company
3. **Configuration User**: Can edit domains and DNS records within their company
4. **Read Only**: View-only access to company data

## API Endpoints

### Companies (Empresas)
```http
GET /api/v1/auth/empresas/          # List companies
POST /api/v1/auth/empresas/         # Create company (Super Admin only)
GET /api/v1/auth/empresas/{id}/     # Get company details
PUT /api/v1/auth/empresas/{id}/     # Update company (Super Admin only)
DELETE /api/v1/auth/empresas/{id}/  # Delete company (Super Admin only)
```

### Users
```http
GET /api/v1/auth/users/             # List users in company
POST /api/v1/auth/users/            # Create user (Company Admin+)
GET /api/v1/auth/users/{id}/        # Get user details
PUT /api/v1/auth/users/{id}/        # Update user (Company Admin+)
DELETE /api/v1/auth/users/{id}/     # Delete user (Company Admin+)
```

### Roles
```http
GET /api/v1/auth/roles/             # List roles (Super Admin only)
POST /api/v1/auth/roles/            # Create role (Super Admin only)
```

### Domains
```http
GET /api/v1/panel/dominios/         # List domains
POST /api/v1/panel/dominios/        # Create domain
GET /api/v1/panel/dominios/{id}/    # Get domain details
PUT /api/v1/panel/dominios/{id}/    # Update domain
DELETE /api/v1/panel/dominios/{id}/ # Delete domain

# Domain-specific actions
GET /api/v1/panel/dominios/{id}/dns_records/  # Get DNS records for domain
POST /api/v1/panel/dominios/{id}/check_dns/   # Trigger DNS check
POST /api/v1/panel/dominios/bulk_update/      # Bulk update domains
GET /api/v1/panel/dominios/stats/             # Get domain statistics
```

### DNS Records
```http
GET /api/v1/panel/dns-records/      # List DNS records
POST /api/v1/panel/dns-records/     # Create DNS record
GET /api/v1/panel/dns-records/{id}/ # Get DNS record details
PUT /api/v1/panel/dns-records/{id}/ # Update DNS record
DELETE /api/v1/panel/dns-records/{id}/ # Delete DNS record

# Bulk operations
POST /api/v1/panel/dns-records/bulk_create/ # Bulk create DNS records
```

### Tags
```http
GET /api/v1/panel/tags/             # List tags
POST /api/v1/panel/tags/            # Create tag
GET /api/v1/panel/tags/{id}/        # Get tag details
PUT /api/v1/panel/tags/{id}/        # Update tag
DELETE /api/v1/panel/tags/{id}/     # Delete tag
```

### Audit Logs
```http
GET /api/v1/panel/audit-logs/       # List audit logs
GET /api/v1/panel/audit-logs/{id}/  # Get audit log details
```

### System Settings
```http
GET /api/v1/panel/system-settings/     # List settings (Super Admin only)
POST /api/v1/panel/system-settings/    # Create setting (Super Admin only)
PUT /api/v1/panel/system-settings/{id}/ # Update setting (Super Admin only)
```

## Example Usage

### Creating a Domain
```http
POST /api/v1/panel/dominios/
Content-Type: application/json

{
    "nombre": "example.com",
    "compliance_level": "high",
    "dmarc_policy": "reject",
    "notification_email": "admin@example.com",
    "tags": ["uuid1", "uuid2"]
}
```

### Creating DNS Records
```http
POST /api/v1/panel/dns-records/
Content-Type: application/json

{
    "dominio": "domain-uuid",
    "tipo": "DMARC",
    "nombre": "_dmarc",
    "valor": "v=DMARC1; p=reject; rua=mailto:dmarc@example.com",
    "ttl": 3600
}
```

### Bulk Creating DNS Records
```http
POST /api/v1/panel/dns-records/bulk_create/
Content-Type: application/json

{
    "domain_id": "domain-uuid",
    "records": [
        {
            "tipo": "SPF",
            "nombre": "@",
            "valor": "v=spf1 include:_spf.google.com ~all",
            "ttl": 3600
        },
        {
            "tipo": "DKIM",
            "nombre": "selector1._domainkey",
            "valor": "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3...",
            "selector": "selector1",
            "ttl": 3600
        }
    ]
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
    "error": "Error message",
    "details": {
        "field": ["Field-specific error message"]
    }
}
```

## Security Features

1. **HttpOnly Cookies**: JWT tokens stored in secure HttpOnly cookies
2. **CSRF Protection**: Built-in CSRF protection for state-changing operations
3. **Role-Based Access Control**: Granular permissions based on user roles
4. **Company Isolation**: Users can only access data from their company
5. **Audit Logging**: All actions are logged for security monitoring
6. **Input Validation**: Comprehensive validation for all inputs

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour

## Pagination

All list endpoints support pagination:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

## Filtering and Search

Most list endpoints support:
- **Filtering**: `?field=value`
- **Search**: `?search=query`
- **Ordering**: `?ordering=field` or `?ordering=-field` (descending)

Example:
```http
GET /api/v1/panel/dominios/?search=example&status=active&ordering=-creado_en
```