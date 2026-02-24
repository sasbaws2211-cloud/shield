# Async Conversion Template - Quick Reference

## Pattern for Converting Service Methods

### Step 1: Update Method Signature
```python
# BEFORE
def my_method(db: Session, param1: str) -> dict:

# AFTER
async def my_method(db: AsyncSession, param1: str) -> dict:
```

### Step 2: Convert All Database Queries
```python
# BEFORE: Single query
user = db.query(User).filter(User.id == user_id).first()

# AFTER: Single query with async
result = await db.execute(select(User).where(User.id == user_id))
user = result.scalars().first()

# BEFORE: Get all records
users = db.query(User).filter(User.active == True).all()

# AFTER: Get all records with async
result = await db.execute(select(User).where(User.active == True))
users = result.scalars().all()

# BEFORE: Count
count = db.query(User).count()

# AFTER: Count with async
result = await db.execute(select(User))
count = len(result.scalars().all())  # Or use func.count()
```

### Step 3: Convert Database Mutations
```python
# BEFORE
db.add(my_object)
db.commit()
db.refresh(my_object)

# AFTER
db.add(my_object)
await db.commit()
await db.refresh(my_object)
```

### Step 4: Convert Nested Service Calls
```python
# BEFORE
result = OtherService.some_method(db, param)

# AFTER
result = await OtherService.some_method(db, param)
```

## Complete Example: Converting admin_service.py

### Before (Sync)
```python
@staticmethod
def approve_officer_registration(
    db: Session,
    registration_id: str,
    admin_id: str,
    ip_address: str
) -> dict:
    """Approve an officer registration."""
    registration = db.query(OfficerRegistration).filter(
        OfficerRegistration.id == registration_id
    ).first()
    
    if not registration:
        raise HTTPException(...)
    
    registration.status = "approved"
    registration.reviewed_by = admin_id
    registration.reviewed_at = datetime.utcnow()
    
    user = db.query(User).filter(User.id == registration.user_id).first()
    user.status = "approved"
    
    audit_log = AuditLog(
        admin_id=admin_id,
        action="approve_officer_registration",
        target_id=registration_id,
        target_type="OfficerRegistration",
        ip_address=ip_address
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "id": registration.id,
        "status": "approved",
        "reviewed_at": registration.reviewed_at
    }
```

### After (Async)
```python
@staticmethod
async def approve_officer_registration(
    db: AsyncSession,
    registration_id: str,
    admin_id: str,
    ip_address: str
) -> dict:
    """Approve an officer registration."""
    # Query registration
    result = await db.execute(
        select(OfficerRegistration).where(
            OfficerRegistration.id == registration_id
        )
    )
    registration = result.scalars().first()
    
    if not registration:
        raise HTTPException(...)
    
    registration.status = "approved"
    registration.reviewed_by = admin_id
    registration.reviewed_at = datetime.utcnow()
    
    # Query user
    user_result = await db.execute(
        select(User).where(User.id == registration.user_id)
    )
    user = user_result.scalars().first()
    user.status = "approved"
    
    # Create audit log
    audit_log = AuditLog(
        admin_id=admin_id,
        action="approve_officer_registration",
        target_id=registration_id,
        target_type="OfficerRegistration",
        ip_address=ip_address
    )
    db.add(audit_log)
    await db.commit()
    
    return {
        "id": registration.id,
        "status": "approved",
        "reviewed_at": registration.reviewed_at
    }
```

## Required Imports for Async Services

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
```

## Remaining Services Conversion Time Estimates

| Service | Methods | Est. Time |
|---------|---------|-----------|
| admin_service.py | 3-4 | 3 min |
| payment_service.py | 3-4 | 4 min |
| notification_service.py | 2-3 | 2 min |
| email_service.py | 6-8 | 2 min |
| stripe_service.py | 2-3 | 2 min |
| **TOTAL** | **~16-22** | **~13 min** |

## Common Query Patterns

### Get by ID
```python
# Async
result = await db.execute(select(Model).where(Model.id == id_value))
obj = result.scalars().first()
```

### Filter with Multiple Conditions
```python
# Async
result = await db.execute(
    select(Model).where(
        Model.status == "active",
        Model.user_id == user_id
    )
)
objs = result.scalars().all()
```

### Filter with OR
```python
from sqlalchemy import or_

result = await db.execute(
    select(Model).where(
        or_(
            Model.status == "pending",
            Model.status == "approved"
        )
    )
)
objs = result.scalars().all()
```

### Join Query
```python
result = await db.execute(
    select(JobPosting).join(User).where(
        User.role == "business"
    )
)
postings = result.scalars().all()
```

### Pagination
```python
page = 1
limit = 20
result = await db.execute(
    select(Model)
    .offset((page - 1) * limit)
    .limit(limit)
)
objects = result.scalars().all()
```

## Testing Async Services

Using pytest-asyncio:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def db_session():
    """Create a test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_approve_officer_registration(db_session):
    """Test officer registration approval."""
    result = await AdminService.approve_officer_registration(
        db=db_session,
        registration_id="test-id",
        admin_id="admin-id",
        ip_address="127.0.0.1"
    )
    assert result["status"] == "approved"
```

## Debugging Async Code

### Check for Missing Awaits
```python
# ❌ WRONG - Missing await
result = db.execute(select(User))

# ✅ CORRECT - Has await
result = await db.execute(select(User))
```

### Check for Missing Async
```python
# ❌ WRONG - Not async function
def process_data(db: AsyncSession):
    result = await db.execute(select(Widget))  # ERROR!

# ✅ CORRECT - Is async function
async def process_data(db: AsyncSession):
    result = await db.execute(select(Widget))
```

### Check Session Type
```python
# ❌ WRONG - Wrong session type
def my_service(db: Session):  # Regular sync Session
    await db.execute(...)  # ERROR!

# ✅ CORRECT - Async session type
async def my_service(db: AsyncSession):  # Async Session
    await db.execute(...)
```

## Helpful Commands

```bash
# Check for sync/await issues
grep -r "db.query" app/services/  # Should find none in async code

grep -r "Session" app/services/  # Should be AsyncSession

# Run type checking
mypy app/services/

# Run tests with asyncio
pytest --asyncio-mode=auto app/

# Format code
black app/
```

## Validation Checklist

Before committing async service conversions:

- [ ] All method signatures have `async def`
- [ ] All database operations use `await`
- [ ] All commits use `await db.commit()`
- [ ] All refreshes use `await db.refresh()`
- [ ] AsyncSession is imported correctly
- [ ] select() is imported from sqlalchemy
- [ ] No db.query() calls remain
- [ ] Error messages are helpful
- [ ] Tests pass with pytest-asyncio
- [ ] Code follows project style guide
