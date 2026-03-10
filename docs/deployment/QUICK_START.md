# ⚡ QUICK START GUIDE

## 🚨 CRITICAL - DO THIS FIRST (30 minutes)

### 1. Remove Hardcoded Credentials
**File**: `backend/static/js/auth.js`
```javascript
// DELETE these lines:
const ADMIN_USERNAME = "sanjay";
const ADMIN_SECRET = "jalsa2008";
```

### 2. Update Admin Credentials
**File**: `backend/.env`
```env
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="GenerateNewStrong$Password123"
```

### 3. Install Security Packages
```bash
pip install -r config/requirements-dev.txt
```

### 4. Use Secure App Version
```bash
cd backend
mv app.py app_original.py
cp app_secure.py app.py
```

### 5. Test Locally
```bash
set FLASK_DEBUG=False
python backend/app.py
curl http://localhost:5000/health
```

---

## 📋 BEFORE DEPLOYMENT

- [ ] Security checklist reviewed? (`docs/security/SECURITY_CHECKLIST.md`)
- [ ] Dependencies updated? (`pip install -r config/requirements-prod.txt`)
- [ ] Credentials removed from JavaScript?
- [ ] Strong password set?
- [ ] All tests passing?

---

## ☁️ QUICK DEPLOYMENT

### Azure (Easiest):
```bash
az group create --name stress-rg --location eastus
az webapp create --resource-group stress-rg --name stress-app --plan stress-plan
az webapp up --resource-group stress-rg --name stress-app
```

### AWS:
```bash
eb init -p python-3.11 stress-detection
eb create stress-env
eb deploy
```

### Docker (Any Cloud):
```bash
docker build -t stress-detection .
docker run -p 5000:5000 stress-detection
```

---

**Status**: 🔴 Start with removing credentials from JavaScript!
