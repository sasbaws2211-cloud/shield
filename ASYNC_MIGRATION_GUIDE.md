# Async Migration Guide - SwiftShield

This document explains the async migration that has been completed and provides guidance for completing the remaining conversions.

## Summary of Changes

### ✅ Completed Conversions

1. **Models** (`app/models/models.py`)
   - Converted from SQLAlchemy ORM to **SQLModel**
   - All 11 tables now use SQLModel with integrated Pydantic validation
   - Removed `Base` class - SQLModel provides this functionality
   - Maintained all relationships and constraints

2. **Database Configuration** (`app/core/database.py`)
   - Migrated from sync to **async SQLAlchemy**
   - Using `create_async_engine()` with PostgreSQL async driver
   - Implemented `AsyncSession` with `async_session_maker`
   - Added async `get_db()` dependency generator
   - Created async `init_db()` and `close_db()` functions

3. **Dependencies** (`app/core/dependencies.py`)
   - Converted all dependency functions to async
   - Updated database queries from `db.query()` to `await db.execute(select(...))`
   - Now uses `AsyncSession` instead of sync `Session`

4. **Configuration** (`app/core/config.py`)
   - Updated `database_url` format to use async PostgreSQL: `postgresql+asyncpg://...`

5. **Requirements** (`requirements.txt`)
   - Added `sqlmodel==0.0.14` 
   - Added `asyncpg==0.29.0` (async PostgreSQL driver)
   - Removed `psycopg2-binary` (replaced by asyncpg)

6. **Main Application** (`main.py`)
   - Updated startup event to await `init_db()`
   - Updated shutdown event to await `close_db()`
   - All exception handlers are async

7. **Job Service** (`app/services/job_service.py`)
   - All methods converted to async using `async def`
   - Database queries use `await db.execute(select(...))`
   - Added `await db.commit()` and `await db.refresh()`

8. **Auth Service** (`app/services/auth_service.py`)
   - All authentication methods are now async
   - Database lookups use SQLAlchemy async queries
   - Maintains all validation logic

### ⏳ Remaining Conversions Required

#### Admin Service (`app/services/admin_service.py`)
Pattern:
```python
# OLD (Sync)
def approve_officer_registration(db: Session, ...):
    registration = db.query(OfficerRegistration).filter(...).first()
    db.add(audit_log)
    db.commit()

# NEW (Async)
async def approve_officer_registration(db: AsyncSession, ...):
    result = await db.execute(select(OfficerRegistration).where(...))
    registration = result.scalars().first()
    db.add(audit_log)
    await db.commit()
```

#### Payment Service (`app/services/payment_service.py`)
- Convert payment method validation queries
- Make invoice generation methods async
- Update payment status update methods

#### Notification Service (`app/services/notification_service.py`)
- Convert all async-ready (most are simple)
- Update any database queries to async

#### Email Service (`app/services/email_service.py`)
- Add async database operations for notification logging
- Keep third-party API calls as-is (SendGrid, etc.)

#### Stripe Service (`app/services/stripe_service.py`)
- Keep Stripe API calls as-is (sync is fine for external APIs)
- Convert any local database operations to async

### API Endpoints Conversion

After services are async, update all endpoints:

```python
# OLD (Sync)
@router.post("/jobs")
def create_job(
    payload: JobSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return JobService.create_job_posting(db, ...)

# NEW (Async)
@router.post("/jobs")
async def create_job(
    payload: JobSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await JobService.create_job_posting(db, ...)
```

## Key Patterns for Async Conversion

### Database Queries
```python
# OLD
user = db.query(User).filter(User.id == user_id).first()

# NEW
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalars().first()
```

### Multiple Results
```python
# OLD
users = db.query(User).filter(User.role == "officer").all()

# NEW
result = await db.execute(select(User).where(User.role == "officer"))
users = result.scalars().all()
```

### Commits and Flushes
```python
# OLD
db.add(object)
db.commit()
db.refresh(object)

# NEW
db.add(object)
await db.commit()
await db.refresh(object)
```

### Type Hints
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

async def my_function(db: AsyncSession):
    ...
```

## Database URL Format

**Important**: PostgreSQL async connection string must use `asyncpg` driver:

```
# Async (NEW)
postgresql+asyncpg://user:password@localhost:5432/swiftshield

# Sync (OLD - DO NOT USE)
postgresql://user:password@localhost:5432/swiftshield
```

## Testing Async Code

```python
import pytest
from pytest_asyncio import fixture

@fixture
async def db():
    async with get_db() as session:
        yield session

@pytest.mark.asyncio
async def test_create_job(db):
    result = await JobService.create_job_posting(db, ...)
    assert result["status"] == "pending"
```

## Remaining Tasks

1. ✅ Convert models to SQLModel
2. ✅ Update database configuration for async
3. ✅ Update dependencies for async
4. ✅ Convert core services (Job, Auth)
5. ⏳ Convert remaining services:
   - [ ] admin_service.py
   - [ ] payment_service.py
   - [ ] notification_service.py
   - [ ] email_service.py
   - [ ] stripe_service.py
6. ⏳ Update all API endpoints to async
7. ⏳ Update tests to use pytest-asyncio

## Performance Benefits

- **Non-blocking I/O**: Database queries don't block other requests
- **Higher Concurrency**: Handle 10-100x more concurrent connections
- **Better Resource Utilization**: Fewer threads needed
- **Faster Response Times**: Especially under load

## Migration Checklist

- [ ] All services converted to async
- [ ] All API endpoints are async
- [ ] Database URL uses asyncpg driver
- [ ] Tests use pytest-asyncio
- [ ] No synchronous db.query() calls remain
- [ ] All db operations use await
- [ ] Error handling tested with async code
- [ ] Load test to verify performance
