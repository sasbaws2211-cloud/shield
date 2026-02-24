# SwiftShield Backend - Implementation TODO

## Phase 1: Database Schema & Models
- [ ] Update drizzle schema with all core tables (User, OfficerRegistration, JobPosting, JobApplication, OfficerShift)
- [ ] Add indexes for performance optimization
- [ ] Create database migration

## Phase 2: Authentication & Authorization
- [ ] Implement JWT token generation and validation
- [ ] Implement bcrypt password hashing
- [ ] Create auth middleware for role-based access control
- [ ] Implement refresh token mechanism
- [ ] Add rate limiting for login endpoint

## Phase 3: Officer Registration
- [ ] Implement POST /auth/register/officer endpoint
- [ ] Add SIA badge number validation (regex pattern)
- [ ] Calculate risk level based on badge expiry
- [ ] Create OfficerRegistration record
- [ ] Add admin notification email trigger
- [ ] Write tests for officer registration

## Phase 4: Business Registration
- [ ] Implement POST /auth/register/business endpoint
- [ ] Add business validation
- [ ] Create admin notification email trigger
- [ ] Write tests for business registration

## Phase 5: Authentication Endpoints
- [ ] Implement POST /auth/login endpoint
- [ ] Implement POST /auth/logout endpoint
- [ ] Implement POST /auth/refresh endpoint
- [ ] Add role-based redirect logic
- [ ] Write tests for auth endpoints

## Phase 6: Job Posting Endpoints
- [ ] Implement POST /business/job-requests endpoint
- [ ] Add 48-hour lead time validation
- [ ] Implement GET /business/job-requests endpoint
- [ ] Write tests for job posting endpoints

## Phase 7: Job Pool & Applications
- [ ] Implement GET /jobs/pool endpoint with pagination
- [ ] Add cache headers for offline support
- [ ] Implement POST /jobs/:id/apply endpoint
- [ ] Add badge expiry constraint validation
- [ ] Add time conflict constraint validation
- [ ] Add guard slot availability check
- [ ] Write tests for job applications

## Phase 8: Officer Shifts
- [ ] Implement GET /officer/shifts endpoint
- [ ] Add ETag support for conditional requests
- [ ] Add cache headers for offline support
- [ ] Write tests for officer shifts

## Phase 9: Admin Registration Management
- [ ] Implement GET /admin/registrations endpoint with filtering
- [ ] Implement PATCH /admin/registrations/:id endpoint
- [ ] Add approval/rejection logic
- [ ] Add admin audit logging
- [ ] Write tests for admin registration endpoints

## Phase 10: Admin Job Posting Management
- [ ] Implement GET /admin/job-postings endpoint with filtering
- [ ] Implement PATCH /admin/job-postings/:id endpoint
- [ ] Add acceptance/rejection logic
- [ ] Write tests for admin job posting endpoints

## Phase 11: Stripe Integration
- [ ] Implement Stripe payment link creation
- [ ] Add Stripe webhook handler for payment confirmation
- [ ] Store payment link ID in database
- [ ] Write tests for Stripe integration

## Phase 12: Email Service Integration
- [ ] Set up email service client (SendGrid/Mailgun)
- [ ] Implement email template rendering
- [ ] Create email sending utility functions
- [ ] Implement all 7 email notification triggers
- [ ] Write tests for email service

## Phase 13: Error Handling & Validation
- [ ] Implement standardized error response format
- [ ] Add input validation for all endpoints
- [ ] Add SQL injection prevention (parameterized queries)
- [ ] Add XSS sanitization
- [ ] Write tests for error handling

## Phase 14: Security & Compliance
- [ ] Add HTTPS enforcement
- [ ] Add HSTS headers
- [ ] Add CORS configuration
- [ ] Implement admin audit logging table
- [ ] Add sensitive data masking (billingEmail, siaBadgeNumber)
- [ ] Write security tests

## Phase 15: Caching & Performance
- [ ] Implement Redis caching layer
- [ ] Add appropriate Cache-Control headers
- [ ] Implement ETag support
- [ ] Write tests for caching

## Phase 16: Documentation & Packaging
- [ ] Create API documentation
- [ ] Create setup and deployment guide
- [ ] Create environment variables guide
- [ ] Package all code and documentation
- [ ] Create README with quick start instructions
