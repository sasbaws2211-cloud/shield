# SwiftShield Backend API

A production-ready FastAPI backend for the SwiftShield workforce management platform connecting security officers with businesses needing security services.

## Features

- **Role-Based Access Control**: Three distinct user roles (Officer, Business, Admin)
- **Officer Management**: Registration, certification tracking, availability management
- **Business Management**: Company profiles, job postings, payment processing
- **Job Posting System**: Create, review, and manage security job opportunities
- **Application Workflow**: Officers apply for jobs with automatic validation
- **Shift Management**: Confirmed shifts with scheduling and tracking
- **Payment Integration**: Stripe payment links for job compensation
- **Email Notifications**: SendGrid integration for transactional emails
- **Admin Dashboard**: Comprehensive admin controls and audit logging
- **Security**: JWT authentication, bcrypt password hashing, rate limiting

## Technology Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with Python-Jose
- **Password Hashing**: Bcrypt
- **Payments**: Stripe API
- **Email**: SendGrid
- **Caching**: Redis
- **Server**: Uvicorn

## Project Structure

```
swiftshield-backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── jobs.py          # Job and application endpoints
│   │   │   ├── admin.py         # Admin management endpoints
│   │   │   └── main.py          # API router initialization
│   │   └── schemas/
│   │       ├── auth.py          # Auth request/response schemas
│   │       ├── jobs.py          # Job schemas
│   │       └── admin.py         # Admin schemas
│   ├── core/
│   │   ├── config.py            # Application settings
│   │   ├── database.py          # Database configuration
│   │   ├── security.py          # JWT and password utilities
│   │   └── dependencies.py      # FastAPI dependency injection
│   ├── models/
│   │   └── models.py            # SQLAlchemy ORM models
│   └── services/
│       ├── auth_service.py      # Authentication business logic
│       ├── job_service.py       # Job management logic
│       ├── admin_service.py     # Admin operations logic
│       ├── email_service.py     # Email notifications
│       └── stripe_service.py    # Stripe payment processing
├── tests/                       # Unit and integration tests
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Redis 6+ (optional, for caching)
- Stripe account
- SendGrid account

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd swiftshield-backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c \"from app.core.database import init_db; init_db()\"
   ```

6. **Run the server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost/swiftshield` |
| `JWT_SECRET` | JWT signing secret (min 256 bits) | `your-secret-key` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `1440` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `30` |
| `STRIPE_SECRET_KEY` | Stripe secret key | `sk_test_...` |
| `STRIPE_PUBLIC_KEY` | Stripe public key | `pk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | `whsec_...` |
| `SENDGRID_API_KEY` | SendGrid API key | `SG....` |
| `SENDGRID_FROM_EMAIL` | Sender email address | `noreply@swiftshield.com` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `["http://localhost:3000"]` |
| `ADMIN_EMAIL` | Admin notification email | `admin@swiftshield.com` |

## API Endpoints

### Authentication
- `POST /api/v1/auth/register/officer` - Register new officer
- `POST /api/v1/auth/register/business` - Register new business
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - User logout

### Jobs
- `GET /api/v1/jobs/pool` - Get available jobs (officers)
- `POST /api/v1/jobs/{job_id}/apply` - Apply to job
- `GET /api/v1/officer/shifts` - Get officer's shifts
- `POST /api/v1/business/job-requests` - Create job posting
- `GET /api/v1/business/job-requests` - Get business job postings

### Admin
- `GET /api/v1/admin/registrations` - List officer registrations
- `PATCH /api/v1/admin/registrations/{id}` - Review registration
- `GET /api/v1/admin/job-postings` - List job postings
- `PATCH /api/v1/admin/job-postings/{id}` - Review job posting

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_access_token>
```

### Token Payload

```json
{
  "sub": "user_id",
  "role": "officer|business|admin",
  "email": "user@example.com",
  "iat": 1725000000,
  "exp": 1725086400
}
```

## Business Logic

### Badge Expiry Constraint
Officers' SIA badges must be valid on the shift date. Risk levels are calculated:
- **Low**: > 180 days until expiry
- **Medium**: 60-180 days until expiry
- **High**: < 60 days or already expired

### Time Conflict Constraint
Officers cannot apply to jobs that overlap with confirmed shifts.

### Guard Slot Tracking
Job postings have a maximum number of guards required. Applications are rejected when slots are full.

### 48-Hour Lead Time
Job postings must have at least 48 hours notice before the start time.

## Email Notifications

The system sends transactional emails for:
- Officer registration approved/rejected
- Job posting accepted/rejected
- Payment link dispatch
- Payment confirmation
- Admin notifications

## Payment Processing

Stripe integration handles:
- Payment link creation for job postings
- Webhook handling for payment confirmation
- Payment status tracking

## Security

- Passwords are hashed with bcrypt (cost factor 12)
- JWT tokens are signed with HS256
- All inputs are validated server-side
- SQL injection prevention via parameterized queries
- CORS protection
- Rate limiting on login endpoint (10 requests/minute)
- Admin audit logging

## Testing

Run the test suite:

```bash
pytest tests/
```

With coverage:

```bash
pytest --cov=app tests/
```

## Deployment

### Docker

Build and run with Docker:

```bash
docker build -t swiftshield .
docker run -p 8000:8000 --env-file .env swiftshield
```

### Production

For production deployment:

1. Set `DEBUG=False` in environment
2. Use a production ASGI server (Gunicorn + Uvicorn)
3. Set up SSL/TLS certificates
4. Configure proper CORS origins
5. Use strong JWT secrets (256+ bits)
6. Enable database backups
7. Set up monitoring and logging

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## Troubleshooting

### Database Connection Error
Ensure PostgreSQL is running and `DATABASE_URL` is correct.

### JWT Token Errors
Verify `JWT_SECRET` is set and consistent across deployments.

### Email Not Sending
Check SendGrid API key and sender email configuration.

### Stripe Webhook Failures
Verify webhook secret matches in Stripe dashboard.

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## License

Proprietary - SwiftShield Platform

## Support

For issues and support, contact: support@swiftshield.com
github account : imustknow221@proton.me