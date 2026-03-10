# ☁️ CLOUD DEPLOYMENT GUIDE

## Overview
This guide covers deploying your stress detection app to Azure, AWS, or similar cloud providers with security best practices.

---

## 🔐 Pre-Deployment Security Checklist

Before deploying:
- [ ] Remove hardcoded credentials from `auth.js`
- [ ] Set strong admin credentials in `.env` (not committed)
- [ ] Update all dependencies to latest versions
- [ ] Enable rate limiting and CSRF protection
- [ ] Set `FLASK_DEBUG=False` for production
- [ ] Configure CORS with specific allowed origins
- [ ] Enable HTTPS/TLS certificates
- [ ] Set up MongoDB authentication
- [ ] Configure session timeouts
- [ ] Test all security features locally

---

## 📦 DEPLOYMENT STEPS

### Step 1: Update Your App

```bash
cd backend
mv app.py app_original.py
cp app_secure.py app.py
```

### Step 2: Update Dependencies

```bash
# Production
pip install -r config/requirements-prod.txt

# Development
pip install -r config/requirements-dev.txt

# Check for vulnerabilities
safety check
```

### Step 3: Production `.env` Configuration

```env
ADMIN_USERNAME="productionadmin123"
ADMIN_PASSWORD="UseA$trong#Password2024!@#" 

MONGO_URI="mongodb+srv://username:password@cluster.mongodb.net/stress_detection_db?retryWrites=true&w=majority"
DB_NAME="stress_detection_prod"

MODEL_PATH="backend/scripts/emotion_model.h5"
FLASK_DEBUG="False"
FLASK_PORT="5000"
SECRET_KEY="3d8211df8a67b6cd669e4816bd65c40e42b605ac6e3a6c2e8d24d87a58882a2e"
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

---

## ☁️ AZURE DEPLOYMENT (RECOMMENDED)

### Prerequisites:
- Azure subscription
- Azure CLI installed

### Deployment:

```bash
# 1. Create Resource Group
az group create --name stress-detection-rg --location eastus

# 2. Create App Service Plan
az appservice plan create \
  --name stress-detection-plan \
  --resource-group stress-detection-rg \
  --sku B1 --is-linux

# 3. Create App Service (Python 3.11)
az webapp create \
  --resource-group stress-detection-rg \
  --plan stress-detection-plan \
  --name stress-detection-app \
  --runtime "PYTHON|3.11"

# 4. Configure App Settings (from .env)
az webapp config appsettings set \
  --resource-group stress-detection-rg \
  --name stress-detection-app \
  --settings \
    ADMIN_USERNAME="productionadmin123" \
    ADMIN_PASSWORD="UseA$trong#Password2024!@#" \
    MONGO_URI="mongodb+srv://..." \
    DB_NAME="stress_detection_prod" \
    FLASK_DEBUG="False" \
    SECRET_KEY="3d8211df..." \
    ALLOWED_ORIGINS="https://yourdomain.com"

# 5. Deploy your code
az webapp up \
  --resource-group stress-detection-rg \
  --name stress-detection-app \
  --runtime PYTHON:3.11

# 6. Enable HTTPS Only
az webapp update \
  --resource-group stress-detection-rg \
  --name stress-detection-app \
  --https-only
```

---

## AWS DEPLOYMENT

### Prerequisites:
- AWS Account
- EB CLI installed

```bash
# 1. Initialize EB application
eb init -p python-3.11 stress-detection --region us-east-1

# 2. Create environment
eb create stress-detection-env

# 3. Deploy
eb deploy

# 4. Enable HTTPS
# In AWS Console: Elastic Beanstalk → Environment → Load Balancer
```

---

## GCP DEPLOYMENT

### Prerequisites:
- Google Cloud Project
- gcloud CLI installed

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/stress-detection

# 2. Deploy to Cloud Run
gcloud run deploy stress-detection \
  --image gcr.io/PROJECT_ID/stress-detection \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 🔒 POST-DEPLOYMENT SECURITY

### Test Health Endpoint
```bash
curl https://yourdomain.com/health
```

### Test Rate Limiting
```bash
# Should get 429 after limit exceeded
for i in {1..20}; do curl -X POST https://yourdomain.com/login; done
```

### Verify HTTPS
```bash
curl -I http://yourdomain.com  # Should redirect to HTTPS
```

### Check Security Headers
```bash
curl -I https://yourdomain.com | grep -E "Strict-Transport|X-Frame|CSP"
```

---

## 🧪 MONITORING

### Azure Monitor
```bash
az monitor app-insights component create \
  --app stress-detection-insights \
  --location eastus \
  --resource-group stress-detection-rg
```

### AWS CloudWatch
- Logs automatically collected
- Set up alarms for errors and high CPU

### GCP Cloud Logging
```bash
gcloud run logs read stress-detection
```

---

**Last Updated**: March 10, 2026
