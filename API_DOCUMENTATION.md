# SwiftShield Backend API Documentation

## Base URL
```
https://api.swiftshield.com/api/v1
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Response Format

All responses are in JSON format with the following structure:

### Success Response
```json
{
  "data": {...},
  "status": "success"
}
```

### Error Response
```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {}
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful request with no content |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - State conflict |
| 422 | Unprocessable Entity - Business rule violation |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## Authentication Endpoints

### Register Officer
**POST** `/auth/register/officer`

Register a new security officer.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "SecurePassword123",
  "sia_badge_number": "SIA-1234567",
  "badge_expiry_date": "2026-12-31T23:59:59Z"
}
```

**Response (201):**
```json
{
  "message": "Registration submitted. Your SIA badge will be verified within 24 hours.",
  "registration_id": "uuid"
}
```

**Validation Rules:**
- `sia_badge_number` must match pattern `/^SIA-\d{7}$/`
- `password` minimum 8 characters
- `email` must be unique
- `badge_expiry_date` must be in the future

---

### Register Business
**POST** `/auth/register/business`

Register a new business account.

**Request Body:**
```json
{
  "company_name": "Apex Security Ltd",
  "contact_person": "Sarah Chen",
  "billing_email": "billing@apex.com",
  "email": "login@apex.com",
  "password": "SecurePassword123"
}
```

**Response (201):**
```json
{
  "message": "Account pending admin approval. You will be notified by email.",
  "user_id": "uuid"
}
```

---

### Login
**POST** `/auth/login`

Authenticate user and receive tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "role": "officer",
    "email": "user@example.com",
    "status": "approved",
    "full_name": "John Doe",
    "sia_badge_number": "SIA-1234567",
    "badge_expiry_date": "2026-12-31T23:59:59Z"
  }
}
```

**Errors:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account not approved

---

### Refresh Token
**POST** `/auth/refresh`

Generate a new access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

---

### Logout
**POST** `/auth/logout`

Logout user (token invalidation handled client-side).

**Response (204):** No Content

---

## Job Endpoints

### Get Job Pool
**GET** `/jobs/pool`

Get all available job postings for officers.

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `limit` (integer, default: 20, max: 50) - Results per page

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "uuid",
      "title": "Night Patrol – Canary Wharf",
      "site_name": "25 North Colonnade",
      "site_address": "Canary Wharf, E14",
      "start_time": "2026-09-10T22:00:00Z",
      "end_time": "2026-09-11T06:00:00Z",
      "guards_required": 2,
      "notes": "CCTV monitoring required",
      "budget_gbp": 300.00,
      "hourly_rate_gbp": 18.75,
      "status": "accepted"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45
  }
}
```

**Auth Required:** Yes (Officer role)

---

### Apply to Job
**POST** `/jobs/{job_id}/apply`

Submit an application for a job posting.

**Path Parameters:**
- `job_id` (string) - Job posting UUID

**Response (201):**
```json
{
  "application_id": "uuid",
  "status": "applied",
  "applied_at": "2026-09-06T10:00:00Z"
}
```

**Errors:**
- `404 Not Found` - Job not found
- `409 Conflict` - Already applied, no slots available
- `422 Unprocessable Entity` - Badge expired or time conflict

**Auth Required:** Yes (Officer role)

---

### Get Officer Shifts
**GET** `/officer/shifts`

Get officer's confirmed shifts.

**Response (200):**
```json
{
  "shifts": [
    {
      "id": "uuid",
      "job_id": "uuid",
      "title": "Warehouse Patrol",
      "site_name": "Tilbury Docks",
      "start_time": "2026-09-10T20:00:00Z",
      "end_time": "2026-09-11T04:00:00Z",
      "hourly_rate_gbp": 17.50,
      "status": "confirmed"
    }
  ]
}
```

**Cache Headers:**
- `Cache-Control: max-age=300, stale-while-revalidate=3600`
- Supports ETag for conditional requests

**Auth Required:** Yes (Officer role)

---

### Create Job Request
**POST** `/business/job-requests`

Submit a new job posting request.

**Request Body:**
```json
{
  "title": "Night Cover – Oxford St Store",
  "site_name": "Oxford Street Store",
  "site_address": "Oxford Street, W1C",
  "start_time": "2026-09-08T20:00:00Z",
  "end_time": "2026-09-09T06:00:00Z",
  "guards_required": 3,
  "notes": "SIA Door Supervisor licence required",
  "budget_gbp": 1500.00
}
```

**Response (201):**
```json
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Your job request has been submitted and is pending admin review."
}
```

**Validation:**
- `start_time` must be at least 48 hours in future
- `end_time` must be after `start_time`
- `guards_required` minimum 1

**Auth Required:** Yes (Business role)

---

### Get Business Job Requests
**GET** `/business/job-requests`

Get all job postings submitted by the business.

**Response (200):**
```json
{
  "job_requests": [
    {
      "id": "uuid",
      "title": "Night Cover – Oxford St",
      "site_name": "Oxford Street, W1C",
      "start_time": "2026-09-08T20:00:00Z",
      "end_time": "2026-09-09T06:00:00Z",
      "guards_required": 3,
      "budget_gbp": 1500.00,
      "status": "accepted",
      "submitted_at": "2026-09-01T09:00:00Z",
      "reject_reason": null,
      "payment_link_sent_at": "2026-09-02T14:30:00Z"
    }
  ]
}
```

**Auth Required:** Yes (Business role)

---

## Admin Endpoints

### List Officer Registrations
**GET** `/admin/registrations`

List all officer registration submissions.

**Query Parameters:**
- `status` (string, default: "all") - Filter by status: pending, approved, rejected, all
- `page` (integer, default: 1)
- `limit` (integer, default: 50)

**Response (200):**
```json
{
  "registrations": [
    {
      "id": "uuid",
      "user_id": "uuid",
      "full_name": "Marcus Webb",
      "email": "marcus@email.com",
      "sia_badge_number": "SIA-4421009",
      "badge_expiry_date": "2027-03-10T00:00:00Z",
      "risk_level": "low",
      "status": "pending",
      "reject_reason": null,
      "submitted_at": "2026-09-01T09:00:00Z",
      "reviewed_by": null,
      "reviewed_at": null
    }
  ],
  "summary": {
    "pending": 3,
    "approved": 1,
    "rejected": 1,
    "total": 5
  }
}
```

**Auth Required:** Yes (Admin role)

---

### Review Officer Registration
**PATCH** `/admin/registrations/{registration_id}`

Approve or reject an officer registration.

**Path Parameters:**
- `registration_id` (string) - Registration UUID

**Request Body:**
```json
{
  "action": "approve",
  "reject_reason": null
}
```

Or for rejection:
```json
{
  "action": "reject",
  "reject_reason": "SIA badge number could not be verified with the licensing authority."
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "status": "approved",
  "reviewed_at": "2026-09-06T11:00:00Z"
}
```

**Validation:**
- `action` must be "approve" or "reject"
- `reject_reason` required for rejection, minimum 10 characters

**Auth Required:** Yes (Admin role)

---

### List Job Postings
**GET** `/admin/job-postings`

List all job postings across all businesses.

**Query Parameters:**
- `status` (string, default: "all") - Filter by status: pending, accepted, rejected, all
- `company` (string) - Filter by partial company name
- `page` (integer, default: 1)
- `limit` (integer, default: 50)

**Response (200):**
```json
{
  "job_postings": [
    {
      "id": "uuid",
      "business_id": "uuid",
      "company_name": "Apex Security Ltd",
      "title": "Night Cover – Oxford St",
      "site_name": "Oxford Street, W1C",
      "start_time": "2026-09-08T20:00:00Z",
      "end_time": "2026-09-09T06:00:00Z",
      "guards_required": 3,
      "budget_gbp": 1500.00,
      "notes": "SIA Door Supervisor licence required",
      "status": "pending",
      "reject_reason": null,
      "submitted_at": "2026-09-01T09:00:00Z",
      "reviewed_by": null,
      "reviewed_at": null,
      "payment_link_sent_at": null
    }
  ],
  "summary": {
    "pending": 3,
    "accepted": 1,
    "rejected": 1,
    "total": 5
  }
}
```

**Auth Required:** Yes (Admin role)

---

### Review Job Posting
**PATCH** `/admin/job-postings/{job_id}`

Accept or reject a job posting.

**Path Parameters:**
- `job_id` (string) - Job posting UUID

**Request Body:**
```json
{
  "action": "accept",
  "reject_reason": null
}
```

Or for rejection:
```json
{
  "action": "reject",
  "reject_reason": "Insufficient lead time. Please resubmit with 14 days notice."
}
```

**Response (200):**
```json
{
  "id": "uuid",
  "status": "accepted",
  "reviewed_at": "2026-09-06T11:00:00Z",
  "stripe_payment_url": "https://pay.stripe.com/..."
}
```

**Side Effects on Accept:**
- Stripe payment link created
- Payment email sent to business
- Job becomes visible in officer job pool

**Validation:**
- `action` must be "accept" or "reject"
- `reject_reason` required for rejection, minimum 10 characters

**Auth Required:** Yes (Admin role)

---

## Rate Limiting

Login endpoint has rate limiting:
- **Limit:** 10 requests per minute per IP address
- **Response:** 429 Too Many Requests with `Retry-After` header

---

## Error Codes

| Code | Meaning |
|------|---------|
| `BADGE_EXPIRED` | Officer's SIA badge has expired |
| `TIME_CONFLICT` | Officer has overlapping confirmed shift |
| `NO_SLOTS` | All guard positions filled |
| `ALREADY_APPLIED` | Officer already applied for this job |
| `INVALID_CREDENTIALS` | Email or password incorrect |
| `ACCOUNT_NOT_APPROVED` | Account status not approved |
| `INSUFFICIENT_PERMISSIONS` | User role not allowed for this action |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |

---

## Webhooks

### Stripe Payment Webhook
**POST** `/webhooks/stripe`

Handles Stripe payment events.

**Events:**
- `payment_intent.succeeded` - Payment completed
- `payment_intent.payment_failed` - Payment failed

---

## Pagination

Paginated endpoints support:
- `page` - Page number (1-indexed)
- `limit` - Results per page

Response includes pagination metadata:
```json
{
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150
  }
}
```

---

## Timestamps

All timestamps are in ISO 8601 UTC format:
```
2026-09-06T10:00:00Z
```

---

## CORS

CORS is enabled for configured origins. Default development origins:
- `http://localhost:3000`
- `http://localhost:5173`

---

## API Versioning

Current version: **v1**

Future versions will be available at `/api/v2`, etc.
