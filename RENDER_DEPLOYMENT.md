# CashBrain Backend - Render Deployment Guide

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Overview](#project-overview)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Environment Variables Setup](#environment-variables-setup)
5. [Database Configuration](#database-configuration)
6. [Deployment Verification](#deployment-verification)
7. [Troubleshooting](#troubleshooting)
8. [Post-Deployment](#post-deployment)

---

## Prerequisites

Before deploying to Render, ensure you have:

- ✅ A [Render account](https://render.com) (free tier available)
- ✅ Your project pushed to GitHub, GitLab, or Gitea
- ✅ MySQL/MariaDB databases (can use [PlanetScale](https://planetscale.com), [AWS RDS](https://aws.amazon.com/rds/), or any MySQL provider)
- ✅ SSH key added to your GitHub account (if using private repos)

---

## Project Overview

**CashBrain Backend** is a Flask-based AI Chatbot API with:

- **Framework**: Flask 3.1.3
- **Database**: SQLAlchemy ORM + MySQL
- **Authentication**: JWT (Flask-JWT-Extended)
- **API Type**: RESTful with 9+ endpoints
- **Python Version**: 3.11

### Key Components

```
API Endpoints:
├── /health                 - Health check
├── /auth/*                 - Authentication routes
├── /income/*               - Income management
├── /expense/*              - Expense management
├── /analysis/*             - Financial analysis
└── /chatbot/*              - AI chatbot endpoints
```

---

## Step-by-Step Deployment

### Step 1: Prepare Your Repository

Ensure your Git repository is ready:

```bash
cd /Users/quannguyen/Documents/CashBrain_Backend

# Verify the main branch is updated
git status
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

**Files automatically created:**
- `render.yaml` - Render service configuration
- `Procfile` - Application startup process
- `runtime.txt` - Python version specification
- `.render/build.sh` - Build script with database setup

### Step 2: Create a Render Account & Connect GitHub

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Sign up or log in
3. Click **"New +"** → **"Web Service"**
4. Select your GitHub repository (CashBrain_Backend)
5. Grant permissions if prompted

### Step 3: Configure the Web Service

**Service Name**: `cashbrain-api`

**Region**: Oregon (or choose closest to your users)

**Branch**: `main` (or your deployment branch)

**Build Command**: (Auto-detected from render.yaml)
```
pip install --upgrade pip && pip install -r requirements.txt
```

**Start Command**: (Auto-detected from render.yaml)
```
gunicorn --workers 3 --worker-class sync --timeout 60 --bind 0.0.0.0:$PORT "run:app"
```

**Plan**: Standard ($7/month) or Free (limited)

### Step 4: Set Environment Variables

In the Render Dashboard, go to **Environment** and add these variables:

#### Critical Variables (Must Set)

| Variable | Value | Example |
|----------|-------|---------|
| `SECRET_KEY` | Random secret string (min 32 chars) | `your-secret-key-32-chars-minimum` |
| `JWT_SECRET_KEY` | Random JWT secret string | `your-jwt-secret-key-change-this` |
| `DATABASE_URL` | MySQL connection string | `mysql+pymysql://user:pass@host/auth_db` |
| `FINANCE_DATABASE_URL` | MySQL connection string | `mysql+pymysql://user:pass@host/finance_db` |
| `CHATBOT_DATABASE_URL` | MySQL connection string | `mysql+pymysql://user:pass@host/chatbot_db` |
| `FLASK_ENV` | `production` | `production` |

#### Generate Secure Keys

For `SECRET_KEY` and `JWT_SECRET_KEY`, generate secure random values:

```bash
# Using Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your keys.

### Step 5: Database Connection Strings

Your MySQL connection string format:

```
mysql+pymysql://username:password@host:port/database_name
```

**Example with PlanetScale**:
```
mysql+pymysql://root:pscale_pw_xxxxxxx@aws.connect.psdb.cloud/cashbrain_auth?ssl_verify_cert=true&ssl_verify_identity=true
```

**Example with AWS RDS**:
```
mysql+pymysql://admin:MyPassword123@cashbrain-db.c9akciq32.us-east-1.rds.amazonaws.com:3306/auth_service_db
```

---

## Environment Variables Setup

### Creating Strong Keys

Use these commands to generate secure keys:

#### On macOS/Linux:

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

#### Using Python:

```python
import secrets

# Generate random hex string
secret_key = secrets.token_hex(32)
jwt_key = secrets.token_hex(32)

print(f"SECRET_KEY: {secret_key}")
print(f"JWT_SECRET_KEY: {jwt_key}")
```

### Database Connection Format

**MySQL Connection String Parameters:**

```
mysql+pymysql://[user]:[password]@[host]:[port]/[database]
```

| Part | Description | Example |
|------|-------------|---------|
| `user` | Database username | `admin` |
| `password` | Database password | `MySecurePass123!` |
| `host` | Database hostname/IP | `db.example.com` |
| `port` | Database port | `3306` (default) |
| `database` | Database name | `auth_service_db` |

---

## Database Configuration

### Recommended Providers

#### 1. **PlanetScale** (Free Tier, Recommended)
- Free tier: 5GB storage, unlimited connections
- Setup: [PlanetScale.com](https://planetscale.com)
- Pros: Easy setup, serverless, free tier is generous
- Connection: `mysql+pymysql://user:password@host.connect.psdb.cloud/dbname?ssl_verify_cert=true&ssl_verify_identity=true`

#### 2. **AWS RDS**
- Free tier: 750 hours/month for db.t3.micro
- Setup: AWS Console → RDS → Create DB
- Pros: Scalable, enterprise-grade
- Connection: `mysql+pymysql://user:password@endpoint.rds.amazonaws.com:3306/dbname`

#### 3. **DigitalOcean MySQL**
- Free trial: $5/month Managed Database
- Setup: DigitalOcean Dashboard
- Connection: `mysql+pymysql://user:password@host:25060/dbname`

### Database Schema Creation

The Render build process automatically creates tables via:

```python
# This runs during build (render.yaml: preDeployCommand)
db.create_all()
```

**Tables created:**
- `user` (auth_service_db)
- `income` (finance_db)
- `expense` (finance_db)
- `chat_history` (chatbot_db)

---

## Deployment Verification

### Step 1: Check Deployment Status

In Render Dashboard:

1. Go to your service page
2. Watch the **Logs** tab for build progress
3. Expected log output:

```
Installing dependencies...
Running database migrations...
Database tables created/verified successfully!
Build completed successfully!
Starting web service...
```

### Step 2: Test Health Endpoint

Once deployment succeeds (status = Live):

```bash
# Test health check (no auth required)
curl https://cashbrain-api.onrender.com/health

# Expected response:
# {"status":"ok"}
```

Replace `cashbrain-api` with your actual service name.

### Step 3: Test Authentication Endpoint

```bash
curl -X POST https://cashbrain-api.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com"
  }'
```

### Step 4: View Real-time Logs

```bash
# SSH into your Render service
render logs -s cashbrain-api -f

# Or use Render Dashboard → Logs tab
```

---

## Troubleshooting

### Issue 1: Deployment Fails During Build

**Symptom**: Build logs show `pip install` failure

**Solution**:
1. Check [requirements.txt](requirements.txt) has valid package versions
2. Verify Python version in [runtime.txt](runtime.txt)
3. Ensure all imports in app files are correct

```bash
# Test locally:
python -m pip install -r requirements.txt
python -c "from app import create_app; app = create_app()"
```

### Issue 2: Database Connection Error

**Symptom**: Logs show `mysql.connector.errors.DatabaseError` or `OperationalError`

**Solution**:
1. Verify `DATABASE_URL` format is correct
2. Test connection locally:

```bash
python3 << EOF
import os
from sqlalchemy import create_engine

db_url = "YOUR_DATABASE_URL_HERE"
engine = create_engine(db_url)
conn = engine.connect()
print("✅ Database connection successful!")
conn.close()
EOF
```

3. Check database firewall allows Render's IP range

### Issue 3: 502 Bad Gateway

**Symptom**: API returns 502 error

**Solution**:
1. Check logs for application errors:
   ```bash
   # In Render Dashboard → Logs
   # Look for Flask startup errors
   ```

2. Verify port binding:
   ```bash
   # Ensure your app listens on 0.0.0.0:$PORT
   # (This is handled by gunicorn in Procfile)
   ```

3. Check secret keys are set:
   ```bash
   # In Render Dashboard → Environment
   # Verify SECRET_KEY and JWT_SECRET_KEY exist
   ```

### Issue 4: Timeout Errors

**Symptom**: Requests timeout (>60s)

**Solution**:
1. Increase timeout in [render.yaml](render.yaml):
   ```yaml
   startCommand: gunicorn --timeout 120 ...
   ```

2. Check database queries are optimized
3. Scale up to higher plan if load is high

### Issue 5: SSL Certificate Errors

**Symptom**: `SSL: CERTIFICATE_VERIFY_FAILED` when connecting to MySQL

**Solution**:
1. For PlanetScale, add SSL parameters to connection string:
   ```
   ?ssl_verify_cert=true&ssl_verify_identity=true
   ```

2. For other providers, try:
   ```
   ?ssl_ca=/etc/ssl/certs/ca-certificates.crt
   ```

---

## Post-Deployment

### 1. Set Custom Domain

In Render Dashboard → Your Service → Custom Domains:

```
api.yourapp.com  →  cashbrain-api.onrender.com
```

### 2. Enable Auto-Deploy

Settings → Auto-Deploy:
- Select `main` branch
- Deploys automatically on each push

### 3. Monitor Performance

Render Dashboard → Metrics:
- CPU usage
- Memory usage
- Response time
- Error rate

### 4. Setup Continuous Monitoring

Example monitoring with alerts:

```bash
# Create monitoring endpoint
curl -m 5 https://cashbrain-api.onrender.com/health \
  || echo "Alert: API is down!"
```

### 5. Database Backups

Set up automated backups (database provider dependent):

**PlanetScale**: Automatic 30-day retention
**AWS RDS**: Enable automated backups in console
**DigitalOcean**: Automated backups available

### 6. Logging & Error Tracking (Optional)

Consider adding:
- **Sentry**: For error tracking
- **LogRocket**: For session replay
- **Datadog**: For monitoring

Add to requirements.txt:

```
sentry-sdk==2.0.0
```

Initialize in app/__init__.py:

```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1
)
```

---

## Useful Commands

### View Live Logs

```bash
# Last 100 lines
curl https://api.render.com/v1/services/<service-id>/logs \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

### Manual Deploy Trigger

```bash
git push origin main  # Automatic with auto-deploy enabled
```

### Access Environment Variables

```bash
# Cannot be accessed directly
# But you can log them in app startup for debugging
```

### Database Query Tools

**PlanetScale CLI**:
```bash
pscale mysql cashbrain_db --execute "SELECT * FROM user LIMIT 5;"
```

**MySQL CLI**:
```bash
mysql -h db.example.com -u admin -p database_name
```

---

## Security Checklist

- [ ] `SECRET_KEY` is random 32+ character hex string
- [ ] `JWT_SECRET_KEY` is random 32+ character hex string
- [ ] Database password is strong (12+ chars, mixed case, numbers, symbols)
- [ ] Database firewall allows only Render's IPs
- [ ] HTTPS is enabled (Render provides free SSL)
- [ ] No credentials in git history or .env files
- [ ] `.env` file is in `.gitignore`
- [ ] JWT tokens use short expiration times
- [ ] API endpoints validate input (CSRF, input sanitization)

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Flask Docs**: https://flask.palletsprojects.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **JWT Docs**: https://flask-jwt-extended.readthedocs.io/

---

## Deployment Checklist

Before clicking "Deploy":

- [ ] All files committed to Git
- [ ] `render.yaml` exists in root
- [ ] `Procfile` exists in root
- [ ] `runtime.txt` exists with Python version
- [ ] `requirements.txt` includes `gunicorn`
- [ ] Environment variables are set:
  - [ ] `SECRET_KEY`
  - [ ] `JWT_SECRET_KEY`
  - [ ] `DATABASE_URL`
  - [ ] `FINANCE_DATABASE_URL`
  - [ ] `CHATBOT_DATABASE_URL`
  - [ ] `FLASK_ENV=production`
- [ ] Databases are created and accessible
- [ ] Health endpoint responds: `GET /health`

---

## FAQ

**Q: Can I use the free tier?**
A: Yes, but it auto-pauses after 15 minutes of inactivity. Use Standard ($7/month) for production.

**Q: How do I update my API after deployment?**
A: Push to `main` branch. Render auto-deploys with auto-deploy enabled.

**Q: Can I have multiple environments (dev, prod)?**
A: Yes! Create separate Render services pointing to different branches/databases.

**Q: What if my database gets corrupted?**
A: Restore from automated backups (set up in your database provider).

**Q: How do I scale for more users?**
A: Upgrade Render plan (more workers) and add database read replicas.

---

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Render account
3. ✅ Configure environment variables
4. ✅ Deploy web service
5. ✅ Test health endpoint
6. ✅ Monitor logs for 24 hours
7. ✅ Set up domain and monitoring

**Happy deploying! 🚀**

