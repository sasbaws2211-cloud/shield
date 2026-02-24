# SwiftShield Backend - Documentation Summary

## Architecture
- **Frontend:** React (Vite) + TanStack Query PWA
- **Backend:** RESTful JSON API (Express)
- **Database:** PostgreSQL
- **Cache:** Redis (cache/queues)
- **Payments:** Stripe
- **Email:** SendGrid/Mailgun

## Three User Roles
1. **Officer** - SIA-licensed security professional
2. **Business** - Corporate client posting security job requests
3. **Admin** - Platform operator approving registrations and job postings

## Core Data Models
1. **User** - Polymorphic across roles with role-specific fields
2. **OfficerRegistration** - Staging table for registration submissions
3. **JobPosting** - Job listings created by business, reviewed by admin
4. **JobApplication** - Officer applications to jobs
5. **OfficerShift** - Confirmed shifts for offline display

## Key Business Rules
1. **Badge Expiry Constraint** - Officer's SIA badge must be valid on shift date
   - Risk levels: low (>180 days), medium (60-180 days), high (<60 days or expired)
2. **Time Conflict Constraint** - Officer cannot apply to overlapping shifts
3. **Guard Slot Tracking** - Track confirmed applications against guardsRequired
4. **Status Machines** - Job posting and officer registration have defined state flows

## API Endpoints (v1)
- **Auth:** POST /auth/login, /auth/register/officer, /auth/register/business, /auth/logout, /auth/refresh
- **Jobs:** GET /jobs/pool, POST /jobs/:id/apply
- **Officer:** GET /officer/shifts
- **Business:** POST /business/job-requests, GET /business/job-requests
- **Admin:** GET/PATCH /admin/registrations/:id, GET/PATCH /admin/job-postings/:id

## Security Requirements
- JWT with 24-hour access token, 30-day refresh token
- bcrypt hashing (cost 12+) or argon2id
- Role-based access control (RBAC)
- Rate limiting on login (10 req/min per IP)
- HTTPS enforced, HSTS header required
- Input validation and sanitization
- Parameterized SQL queries
- Admin audit logging

## External Integrations
1. **Stripe** - Payment links for job postings
2. **Email Service** - Transactional emails via SendGrid/Mailgun

## Caching Strategy
- GET /jobs/pool: max-age=120, stale-while-revalidate=600
- GET /officer/shifts: max-age=300, stale-while-revalidate=3600
- GET /business/job-requests: max-age=60, stale-while-revalidate=300
- Admin routes: no-cache
- Mutations: no-store

## Email Notifications
1. Officer approved - tpl_officer_welcome
2. Officer rejected - tpl_officer_rejected
3. Job accepted (payment) - tpl_job_accepted_payment
4. Job rejected - tpl_job_rejected
5. New officer registration (admin) - tpl_admin_new_officer
6. New job posting (admin) - tpl_admin_new_job
7. Payment confirmed - tpl_payment_confirmed
