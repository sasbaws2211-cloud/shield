# SwiftShield Backend - Deployment Guide

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] SSL/TLS certificates obtained
- [ ] Stripe and SendGrid accounts configured
- [ ] Redis instance provisioned
- [ ] Monitoring and logging setup
- [ ] Backup strategy defined
- [ ] Security audit completed

## Local Development

### Quick Start with Docker Compose

```bash
# Clone repository
git clone <repo-url>
cd swiftshield-backend

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec app python -c "from app.core.database import init_db; init_db()"

# View logs
docker-compose logs -f app
```

Services will be available at:
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/api/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### AWS ECS Deployment

1. **Build and push Docker image**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -t swiftshield-backend .
   docker tag swiftshield-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/swiftshield-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/swiftshield-backend:latest
   ```

2. **Create ECS task definition**
   ```json
   {
     "family": "swiftshield-backend",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "swiftshield-backend",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/swiftshield-backend:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "hostPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "ENVIRONMENT",
             "value": "production"
           }
         ],
         "secrets": [
           {
             "name": "DATABASE_URL",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:swiftshield/database-url"
           },
           {
             "name": "JWT_SECRET",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:swiftshield/jwt-secret"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/swiftshield-backend",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

3. **Create ECS service**
   ```bash
   aws ecs create-service \
     --cluster swiftshield \
     --service-name swiftshield-backend \
     --task-definition swiftshield-backend \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
     --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:<account-id>:targetgroup/swiftshield/xxx,containerName=swiftshield-backend,containerPort=8000"
   ```

### Heroku Deployment

1. **Create Heroku app**
   ```bash
   heroku create swiftshield-backend
   ```

2. **Add buildpack**
   ```bash
   heroku buildpacks:add heroku/python
   ```

3. **Set environment variables**
   ```bash
   heroku config:set DATABASE_URL=postgresql://...
   heroku config:set JWT_SECRET=your-secret-key
   heroku config:set STRIPE_SECRET_KEY=sk_live_...
   heroku config:set SENDGRID_API_KEY=SG...
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Run migrations**
   ```bash
   heroku run python -c "from app.core.database import init_db; init_db()"
   ```

### Railway Deployment

1. **Connect GitHub repository**
   - Link your GitHub account to Railway
   - Select the repository

2. **Configure environment**
   - Add environment variables in Railway dashboard
   - Set `ENVIRONMENT=production`

3. **Deploy**
   - Railway auto-deploys on push to main branch

### DigitalOcean App Platform

1. **Create app**
   ```bash
   doctl apps create --spec app.yaml
   ```

2. **app.yaml configuration**
   ```yaml
   name: swiftshield-backend
   services:
   - name: api
     github:
       repo: username/swiftshield-backend
       branch: main
     build_command: pip install -r requirements.txt
     run_command: uvicorn main:app --host 0.0.0.0 --port 8080
     http_port: 8080
     envs:
     - key: ENVIRONMENT
       value: production
   databases:
   - name: postgres
     engine: PG
     version: "15"
   ```

## Database Setup

### PostgreSQL

```bash
# Create database
createdb swiftshield

# Create user
createuser swiftshield_user

# Set password
psql -c "ALTER USER swiftshield_user WITH PASSWORD 'secure_password';"

# Grant privileges
psql -c "GRANT ALL PRIVILEGES ON DATABASE swiftshield TO swiftshield_user;"

# Connection string
postgresql://swiftshield_user:secure_password@localhost:5432/swiftshield
```

### Database Migrations

```bash
# Initialize database
python -c "from app.core.database import init_db; init_db()"

# Verify tables
psql swiftshield -c "\\dt"
```

## Redis Setup

### Local Redis

```bash
# Install
brew install redis  # macOS
apt-get install redis-server  # Ubuntu

# Start
redis-server

# Verify
redis-cli ping  # Should return PONG
```

### AWS ElastiCache

```bash
# Create Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id swiftshield-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 1

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id swiftshield-redis \
  --show-cache-node-info
```

## SSL/TLS Setup

### Let's Encrypt with Certbot

```bash
# Install Certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot certonly --standalone -d api.swiftshield.com

# Auto-renewal
certbot renew --dry-run
```

### AWS Certificate Manager

```bash
# Request certificate
aws acm request-certificate \
  --domain-name api.swiftshield.com \
  --validation-method DNS
```

## Monitoring & Logging

### CloudWatch Logs

```bash
# Create log group
aws logs create-log-group --log-group-name /swiftshield/backend

# Create log stream
aws logs create-log-stream \
  --log-group-name /swiftshield/backend \
  --log-stream-name production
```

### Application Monitoring

Configure in `app/core/config.py`:
```python
import logging
from pythonjsonlogger import jsonlogger

# JSON logging for CloudWatch
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Sentry Integration

```bash
pip install sentry-sdk

# In main.py
import sentry_sdk
sentry_sdk.init(
    dsn="https://<key>@sentry.io/<project>",
    traces_sample_rate=0.1,
    environment="production"
)
```

## Security Hardening

### API Rate Limiting

```python
# In main.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(...):
    pass
```

### HTTPS Redirect

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.swiftshield.com"]
)
```

### Security Headers

```python
from fastapi.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

## Backup Strategy

### Database Backups

```bash
# PostgreSQL backup
pg_dump swiftshield > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore
psql swiftshield < backup_20260906_120000.sql

# AWS RDS automated backups
aws rds modify-db-instance \
  --db-instance-identifier swiftshield-db \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00"
```

### S3 Backup

```bash
# Backup to S3
aws s3 cp backup.sql s3://swiftshield-backups/$(date +%Y/%m/%d)/backup.sql
```

## Health Checks

### Application Health

```bash
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "app": "SwiftShield Backend",
  "version": "1.0.0"
}
```

### Database Health

```python
@app.get("/health/db")
async def db_health(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}
```

## Scaling

### Horizontal Scaling

1. **Load Balancer Setup**
   - Configure ALB/NLB to distribute traffic
   - Health check: `/health`
   - Stickiness: Disabled (stateless API)

2. **Auto-Scaling**
   ```bash
   # AWS Auto Scaling Group
   aws autoscaling create-auto-scaling-group \
     --auto-scaling-group-name swiftshield-asg \
     --launch-template LaunchTemplateName=swiftshield \
     --min-size 2 \
     --max-size 10 \
     --desired-capacity 3
   ```

### Database Scaling

- Use read replicas for read-heavy operations
- Connection pooling with PgBouncer
- Archive old audit logs to separate table

## Rollback Procedure

```bash
# Identify previous working version
docker images | grep swiftshield-backend

# Rollback to previous version
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/swiftshield-backend:v1.0.0
docker tag <account-id>.dkr.ecr.us-east-1.amazonaws.com/swiftshield-backend:v1.0.0 latest

# Update ECS service
aws ecs update-service \
  --cluster swiftshield \
  --service swiftshield-backend \
  --force-new-deployment
```

## Post-Deployment Verification

```bash
# Check API health
curl https://api.swiftshield.com/health

# Verify database connection
curl https://api.swiftshield.com/health/db

# Test authentication
curl -X POST https://api.swiftshield.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'

# Check logs
docker logs swiftshield-backend
# or
aws logs tail /swiftshield/backend --follow
```

## Troubleshooting

### Connection Refused
- Verify database is running and accessible
- Check `DATABASE_URL` format
- Verify security groups/firewall rules

### JWT Token Errors
- Ensure `JWT_SECRET` is consistent across deployments
- Check token expiration time
- Verify algorithm matches

### Stripe Webhook Failures
- Verify webhook secret in Stripe dashboard
- Check webhook endpoint URL is publicly accessible
- Review Stripe event logs

### Email Not Sending
- Verify SendGrid API key
- Check sender email is verified
- Review SendGrid activity log

## Maintenance

### Regular Tasks

- **Daily**: Monitor error logs
- **Weekly**: Review performance metrics
- **Monthly**: Database maintenance, backup verification
- **Quarterly**: Security updates, dependency updates
- **Annually**: Full security audit

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update dependencies
pip install --upgrade -r requirements.txt

# Test thoroughly before deploying
pytest tests/
```
