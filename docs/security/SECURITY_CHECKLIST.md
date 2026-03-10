# 🔐 Security Checklist for Cloud Deployment

## CRITICAL (Must Fix Before Deployment)

- [ ] **Remove hardcoded credentials from `auth.js`**
  - File: `backend/static/js/auth.js` (lines with ADMIN_USERNAME, ADMIN_SECRET)
  - Send credentials only via secure API, never hardcode client-side

- [ ] **Set strong admin credentials in `.env`** 
  - Use complex password: min 16 chars, uppercase, numbers, symbols
  - Never commit `.env` to git - add to `.gitignore`

- [ ] **Add `.env` to `.gitignore`**
  ```
  .env
  *.env
  __pycache__/
  *.pyc
  models/
  node_modules/
  ```

- [ ] **Configure CORS properly**
  - Specify exact allowed origins
  - Remove `supports_credentials=True` unless necessary

- [ ] **Enable HTTPS/TLS**
  - Use cloud provider's SSL certificates (Azure App Service, AWS, etc.)
  - Redirect HTTP → HTTPS

- [ ] **Add Rate Limiting**
  - Install: `pip install Flask-Limiter`
  - Limit login attempts: 5 attempts per 15 minutes per IP

- [ ] **Add CSRF Protection**
  - Install: `pip install Flask-WTF`
  - Add CSRF tokens to forms

- [ ] **Protect `/video_feed` endpoint**
  - Add session check before streaming
  - Consider disabling in production

- [ ] **Set `FLASK_DEBUG=False` in production**
  - Ensure `.env` has `FLASK_DEBUG="False"`

- [ ] **Add Session Timeout**
  - Configure `PERMANENT_SESSION_LIFETIME = 30 minutes`
  - Use `sessions.permanent = True`

## HIGH (Should Fix Before Deployment)

- [ ] **Update dependencies to latest secure versions**
  - `pip install --upgrade Flask tensorflow flask-cors flask-limiter flask-wtf`
  - Test thoroughly after updates

- [ ] **Implement password complexity requirements**
  - Min 8 characters, at least 1 uppercase, 1 number, 1 special char
  - Use `python-validator` package

- [ ] **Add comprehensive input validation**
  - Validate username: alphanumeric + underscore only
  - Email validation
  - Password strength checking

- [ ] **Secure MongoDB connection**
  - Use authentication in production: `mongodb://user:pass@host:port/`
  - Enable MongoDB network restrictions (IP whitelist)
  - Use connection pooling

- [ ] **Add logging & monitoring**
  - Log all authentication attempts
  - Log all admin actions
  - Monitor failed login attempts

## MEDIUM (Recommended for Security Hardening)

- [ ] **Implement API key authentication for mobile/external clients**
  - Use JWT tokens instead of session cookies if needed

- [ ] **Add Content Security Policy (CSP) headers**
  ```python
  @app.after_request
  def set_security_headers(response):
      response.headers['Content-Security-Policy'] = "default-src 'self'"
      response.headers['X-Content-Type-Options'] = 'nosniff'
      response.headers['X-Frame-Options'] = 'DENY'
      return response
  ```

- [ ] **Set secure cookie flags**
  ```python
  SESSION_COOKIE_SECURE = True  # HTTPS only
  SESSION_COOKIE_HTTPONLY = True  # No JS access
  SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
  ```

- [ ] **Implement audit logging for sensitive operations**
  - User creation/deletion
  - Password changes
  - Role changes

- [ ] **Add health check endpoint**
  - Used by load balancers to verify app status
  - Doesn't require authentication

- [ ] **Enable dependency vulnerability scanning**
  - Use `pip install safety` and run: `safety check`
  - Consider GitHub Security or Snyk

## LOW (Future Improvements)

- [ ] **Two-Factor Authentication (2FA)**
- [ ] **User activity audit trail**
- [ ] **Database encryption at rest**
- [ ] **API versioning strategy**
- [ ] **Implement API request signing**
- [ ] **Add request timeout protection**

---

## Cloud Deployment Specific

### For Azure App Service:
- Enable HTTPS only (built-in)
- Use Managed Identity for database auth
- Enable IP restrictions if needed
- Use Key Vault for secrets management

### For AWS/GCP:
- Use WAF (Web Application Firewall)
- Enable DDoS protection
- Use secrets manager instead of .env files
- Enable VPC/network isolation

---

## Before Going Live

1. **Security Audit**: Have someone review `/api/*` endpoints
2. **Penetration Testing**: Test for OWASP Top 10 vulnerabilities
3. **Load Testing**: Ensure rate limiting works properly
4. **Backup Strategy**: Document database backup plan
5. **Incident Response**: Have plan if credentials compromised

---

**Last Updated**: March 10, 2026
**Status**: ⚠️ NOT YET PRODUCTION READY
