# Render Deployment - Quick Reference

## 🚀 Quick Start (5 minutes)

### 1. Generate Secure Keys
```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### 2. Set Database URL
```
mysql+pymysql://username:password@host:port/database_name
```

### 3. Push to GitHub
```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

### 4. Deploy on Render
- Go to dashboard.render.com
- Click "New Web Service"
- Select your GitHub repo
- Set environment variables
- Click "Deploy"

---

## 📋 Environment Variables Needed

| Variable | Required | Example |
|----------|----------|---------|
| `SECRET_KEY` | ✅ | `a1b2c3d4e5f6...` |
| `JWT_SECRET_KEY` | ✅ | `x9y8z7w6v5u4...` |
| `DATABASE_URL` | ✅ | `mysql+pymysql://user:pass@host/auth_db` |
| `FINANCE_DATABASE_URL` | ✅ | `mysql+pymysql://user:pass@host/finance_db` |
| `CHATBOT_DATABASE_URL` | ✅ | `mysql+pymysql://user:pass@host/chatbot_db` |
| `FLASK_ENV` | ✅ | `production` |

---

## 🔍 Verify Deployment

```bash
# Health check (public)
curl https://your-service.onrender.com/health

# Should return:
# {"status":"ok"}
```

---

## 📝 Config Files Created

- ✅ `render.yaml` - Service configuration
- ✅ `Procfile` - Application startup
- ✅ `runtime.txt` - Python version
- ✅ `.render/build.sh` - Build script
- ✅ `.env.example` - Environment template
- ✅ `RENDER_DEPLOYMENT.md` - Full guide
- ✅ `requirements.txt` - Updated with gunicorn

---

## 🐛 Troubleshooting

**Build fails?**
- Check `requirements.txt` syntax
- Run locally: `pip install -r requirements.txt`

**Database won't connect?**
- Verify connection string format
- Check database firewall/whitelist

**502 errors?**
- Check logs in Render dashboard
- Verify `SECRET_KEY` and `JWT_SECRET_KEY` are set

---

## 📚 Full Guide

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete documentation.
