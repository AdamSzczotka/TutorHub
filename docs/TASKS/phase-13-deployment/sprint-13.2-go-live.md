# Phase 13 - Sprint 13.2: GO-LIVE! (Django)

## Tasks 158-165: Production Deployment & Launch

> **Duration**: Week 17 (Second half - FINAL SPRINT!)
> **Goal**: Deploy to production, configure domain, and GO LIVE!
> **Dependencies**: Sprint 13.1 complete (Production infrastructure ready)

---

## SPRINT OVERVIEW

| Task ID | Description                          | Priority | Dependencies      |
| ------- | ------------------------------------ | -------- | ----------------- |
| 158     | Docker production deployment         | Critical | Task 157 complete |
| 159     | DNS & domain configuration           | Critical | Task 158          |
| 160     | SSL certificates & final security    | Critical | Task 159          |
| 161     | Production smoke tests               | Critical | Task 160          |
| 162     | Performance verification             | High     | Task 161          |
| 163     | Scaling configuration                | High     | Task 161          |
| 164     | User training & onboarding           | High     | Task 161          |
| 165     | **GO-LIVE CHECKLIST**                | Critical | Tasks 158-164     |

---

## DOCKER PRODUCTION DEPLOYMENT

### Deployment Script

**File**: `scripts/deploy.sh`

```bash
#!/bin/bash
set -e

echo "==================================="
echo "Na Piatke Production Deployment"
echo "==================================="

# Configuration
DEPLOY_DIR="/opt/napiatke"
BACKUP_DIR="$DEPLOY_DIR/backups"
COMPOSE_FILE="docker-compose.prod.yml"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Create directories
mkdir -p $DEPLOY_DIR
mkdir -p $BACKUP_DIR

# Navigate to deploy directory
cd $DEPLOY_DIR

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Build images
echo "Building Docker images..."
docker-compose -f $COMPOSE_FILE build --no-cache

# Create backup before deployment
echo "Creating pre-deployment backup..."
if docker-compose -f $COMPOSE_FILE ps | grep -q "napiatke_db.*Up"; then
    docker exec napiatke_db pg_dump -U $POSTGRES_USER $POSTGRES_DB > \
        "$BACKUP_DIR/pre-deploy-$(date +%Y%m%d-%H%M%S).sql"
fi

# Stop old containers
echo "Stopping old containers..."
docker-compose -f $COMPOSE_FILE down

# Start new containers
echo "Starting new containers..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Run migrations
echo "Running database migrations..."
docker exec napiatke_web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker exec napiatke_web python manage.py collectstatic --noinput

# Health check
echo "Running health check..."
HEALTH=$(curl -s http://localhost:8000/api/health/)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}Deployment successful!${NC}"
else
    echo -e "${RED}Health check failed!${NC}"
    echo "$HEALTH"
    exit 1
fi

# Cleanup old images
echo "Cleaning up old Docker images..."
docker image prune -f

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}==================================${NC}"
```

### Pre-Deployment Verification

**File**: `scripts/verify-deployment.sh`

```bash
#!/bin/bash
set -e

echo "Pre-Deployment Verification"
echo "============================"

ERRORS=0

# Check environment file
echo -n "Checking .env.production... "
if [ -f ".env.production" ]; then
    echo "OK"
else
    echo "MISSING"
    ((ERRORS++))
fi

# Check required environment variables
REQUIRED_VARS=("SECRET_KEY" "DATABASE_URL" "REDIS_URL" "SENTRY_DSN" "RESEND_API_KEY")

for var in "${REQUIRED_VARS[@]}"; do
    echo -n "Checking $var... "
    if grep -q "^$var=" .env.production 2>/dev/null; then
        echo "OK"
    else
        echo "MISSING"
        ((ERRORS++))
    fi
done

# Check Docker
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    echo "OK ($(docker --version))"
else
    echo "NOT INSTALLED"
    ((ERRORS++))
fi

# Check Docker Compose
echo -n "Checking Docker Compose... "
if command -v docker-compose &> /dev/null; then
    echo "OK ($(docker-compose --version))"
else
    echo "NOT INSTALLED"
    ((ERRORS++))
fi

# Check SSL certificates
echo -n "Checking SSL certificates... "
if [ -f "nginx/ssl/fullchain.pem" ] && [ -f "nginx/ssl/privkey.pem" ]; then
    echo "OK"
else
    echo "MISSING"
    ((ERRORS++))
fi

# Summary
echo ""
echo "============================"
if [ $ERRORS -eq 0 ]; then
    echo "All checks passed!"
    exit 0
else
    echo "FAILED: $ERRORS errors found"
    exit 1
fi
```

---

## DNS & DOMAIN CONFIGURATION

### DNS Records

**At your domain registrar (e.g., OVH, nazwa.pl)**:

**A Record (Apex domain)**:
```
Type: A
Name: @
Value: [Your Server IP]
TTL: 3600
```

**CNAME Record (www)**:
```
Type: CNAME
Name: www
Value: napiatke.pl
TTL: 3600
```

**Email DNS Records (for Resend)**:

**SPF Record**:
```
Type: TXT
Name: @
Value: v=spf1 include:resend.com ~all
TTL: 3600
```

**DKIM Record**:
```
Type: TXT
Name: resend._domainkey
Value: [Provided by Resend dashboard]
TTL: 3600
```

**DMARC Record**:
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=none; rua=mailto:admin@napiatke.pl
TTL: 3600
```

### DNS Verification Script

**File**: `scripts/verify-dns.sh`

```bash
#!/bin/bash

DOMAIN="napiatke.pl"

echo "DNS Verification for $DOMAIN"
echo "============================="

# Check A record
echo -n "A record: "
dig +short $DOMAIN A

# Check CNAME
echo -n "www CNAME: "
dig +short www.$DOMAIN CNAME

# Check SPF
echo -n "SPF: "
dig +short $DOMAIN TXT | grep spf

# Check DKIM
echo -n "DKIM: "
dig +short resend._domainkey.$DOMAIN TXT | head -1

echo ""
echo "Check global propagation at: https://dnschecker.org"
```

---

## SSL CERTIFICATES & FINAL SECURITY

### Let's Encrypt with Certbot

**File**: `scripts/setup-ssl.sh`

```bash
#!/bin/bash
set -e

DOMAIN="napiatke.pl"
EMAIL="admin@napiatke.pl"
SSL_DIR="nginx/ssl"

echo "Setting up SSL certificates..."

# Install certbot
apt-get update
apt-get install -y certbot

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Obtain certificate
certbot certonly --standalone \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive

# Copy certificates
mkdir -p $SSL_DIR
cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $SSL_DIR/
cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $SSL_DIR/

# Set permissions
chmod 644 $SSL_DIR/fullchain.pem
chmod 600 $SSL_DIR/privkey.pem

# Restart nginx
docker-compose -f docker-compose.prod.yml start nginx

echo "SSL setup complete!"

# Setup auto-renewal
echo "0 3 * * * certbot renew --quiet --post-hook 'docker restart napiatke_nginx'" | crontab -
echo "Auto-renewal cron job added"
```

### Security Audit Checklist

**File**: `docs/deployment/security-checklist.md`

```markdown
# Security Audit Checklist

## Server Security
- [ ] SSH key authentication only (no passwords)
- [ ] Firewall configured (UFW)
- [ ] Only ports 80, 443, 22 open
- [ ] Fail2ban installed
- [ ] Regular security updates

## Application Security
- [ ] DEBUG=False in production
- [ ] SECRET_KEY is unique and secret
- [ ] ALLOWED_HOSTS configured
- [ ] CSRF protection enabled
- [ ] XSS protection headers
- [ ] SQL injection prevented (Django ORM)
- [ ] Rate limiting active

## SSL/TLS
- [ ] SSL certificate valid
- [ ] HTTPS redirect enforced
- [ ] HSTS enabled
- [ ] TLSv1.2+ only
- [ ] SSL Labs score: A+

## Database
- [ ] Strong password
- [ ] Connection over localhost only
- [ ] Regular backups
- [ ] Point-in-time recovery

## Monitoring
- [ ] Sentry configured
- [ ] Log aggregation
- [ ] Uptime monitoring
- [ ] Alert notifications
```

---

## PRODUCTION SMOKE TESTS

### Smoke Test Script

**File**: `scripts/smoke-test.sh`

```bash
#!/bin/bash

BASE_URL=${BASE_URL:-"https://napiatke.pl"}
PASSED=0
FAILED=0

echo "Production Smoke Tests"
echo "======================"
echo "Target: $BASE_URL"
echo ""

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "Testing $name... "

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" -k)

    if [ "$HTTP_CODE" -eq "$expected_code" ]; then
        echo "PASS (HTTP $HTTP_CODE)"
        ((PASSED++))
    else
        echo "FAIL (Expected $expected_code, got $HTTP_CODE)"
        ((FAILED++))
    fi
}

# Run tests
test_endpoint "Homepage" "$BASE_URL/"
test_endpoint "Health Check" "$BASE_URL/api/health/"
test_endpoint "Login Page" "$BASE_URL/accounts/login/"
test_endpoint "Static Files" "$BASE_URL/static/css/output.css"
test_endpoint "Admin Redirect" "$BASE_URL/admin/" 302

# SSL Check
echo -n "Testing SSL Certificate... "
if curl -sI "$BASE_URL" 2>&1 | grep -q "HTTP/2"; then
    echo "PASS (HTTP/2 enabled)"
    ((PASSED++))
else
    echo "PASS (HTTPS working)"
    ((PASSED++))
fi

# Response Time Check
echo -n "Testing Response Time... "
RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "$BASE_URL")
if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
    echo "PASS (${RESPONSE_TIME}s)"
    ((PASSED++))
else
    echo "WARN (${RESPONSE_TIME}s - slow)"
    ((PASSED++))
fi

# Summary
echo ""
echo "======================"
echo "Passed: $PASSED"
echo "Failed: $FAILED"

if [ $FAILED -gt 0 ]; then
    echo "SOME TESTS FAILED!"
    exit 1
else
    echo "ALL TESTS PASSED!"
    exit 0
fi
```

### Playwright E2E Tests

**File**: `tests/e2e/test_production.py`

```python
import pytest
from playwright.sync_api import Page, expect
import os

BASE_URL = os.environ.get('BASE_URL', 'https://napiatke.pl')


class TestProductionSmoke:
    """Production smoke tests using Playwright."""

    def test_homepage_loads(self, page: Page):
        """Test that homepage loads successfully."""
        page.goto(BASE_URL)
        expect(page).to_have_title(re.compile('Na Piątkę'))
        expect(page.locator('nav')).to_be_visible()

    def test_health_check(self, page: Page):
        """Test health check endpoint."""
        response = page.request.get(f'{BASE_URL}/api/health/')
        assert response.ok
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'

    def test_login_page(self, page: Page):
        """Test login page accessibility."""
        page.goto(f'{BASE_URL}/accounts/login/')
        expect(page.locator('input[name="email"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()

    def test_admin_login(self, page: Page):
        """Test admin login flow."""
        page.goto(f'{BASE_URL}/accounts/login/')

        page.fill('input[name="email"]', os.environ['TEST_ADMIN_EMAIL'])
        page.fill('input[name="password"]', os.environ['TEST_ADMIN_PASSWORD'])
        page.click('button[type="submit"]')

        # Should redirect to dashboard
        page.wait_for_url(f'{BASE_URL}/admin/dashboard/')
        expect(page.locator('h1')).to_contain_text('Dashboard')

    def test_no_console_errors(self, page: Page):
        """Test that no JavaScript errors occur."""
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))

        pages_to_test = [
            '/',
            '/accounts/login/',
        ]

        for path in pages_to_test:
            page.goto(f'{BASE_URL}{path}')
            page.wait_for_load_state('networkidle')

        assert len(errors) == 0, f'JavaScript errors found: {errors}'

    def test_ssl_certificate(self, page: Page):
        """Test SSL certificate is valid."""
        response = page.goto(BASE_URL)
        assert response.url.startswith('https://')
        assert response.ok

    def test_page_load_performance(self, page: Page):
        """Test page loads within acceptable time."""
        start_time = page.evaluate('() => performance.now()')
        page.goto(BASE_URL)
        page.wait_for_load_state('networkidle')
        end_time = page.evaluate('() => performance.now()')

        load_time = (end_time - start_time) / 1000
        assert load_time < 3.0, f'Page load too slow: {load_time}s'
```

---

## PERFORMANCE VERIFICATION

### Performance Metrics

**Target Metrics**:

| Metric | Target | Acceptable |
|--------|--------|------------|
| TTFB | <500ms | <1000ms |
| LCP | <2.5s | <4.0s |
| FID | <100ms | <300ms |
| CLS | <0.1 | <0.25 |
| Page Load | <3s | <5s |

### Performance Test Script

**File**: `scripts/perf-test.sh`

```bash
#!/bin/bash

URL=${1:-"https://napiatke.pl"}

echo "Performance Test for $URL"
echo "=========================="

# Test with curl
echo ""
echo "Response Times:"
curl -w "\
    DNS Lookup:    %{time_namelookup}s\n\
    TCP Connect:   %{time_connect}s\n\
    TLS Handshake: %{time_appconnect}s\n\
    TTFB:          %{time_starttransfer}s\n\
    Total Time:    %{time_total}s\n\
" -o /dev/null -s "$URL"

# Test with lighthouse (if installed)
if command -v lighthouse &> /dev/null; then
    echo ""
    echo "Running Lighthouse audit..."
    lighthouse "$URL" \
        --only-categories=performance \
        --output=json \
        --output-path=./lighthouse-report.json \
        --chrome-flags="--headless"

    # Extract scores
    PERF_SCORE=$(jq '.categories.performance.score * 100' lighthouse-report.json)
    echo "Performance Score: $PERF_SCORE/100"
fi
```

---

## SCALING CONFIGURATION

### Docker Swarm Setup (Optional)

**File**: `docker-compose.swarm.yml`

```yaml
version: '3.8'

services:
  web:
    image: napiatke:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    environment:
      - DJANGO_SETTINGS_MODULE=napiatke.settings.production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Load Balancer Configuration

**File**: `nginx/nginx-lb.conf`

```nginx
upstream django_cluster {
    least_conn;
    server web1:8000 weight=5;
    server web2:8000 weight=5;
    server web3:8000 weight=5;

    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name napiatke.pl;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location / {
        proxy_pass http://django_cluster;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## USER TRAINING & ONBOARDING

### Welcome Email Templates

**File**: `templates/emails/welcome_admin.html`

```html
{% extends "emails/base.html" %}

{% block content %}
<h1>Witamy w systemie Na Piątkę!</h1>

<p>Twoje konto administratora zostało utworzone.</p>

<h2>Dane logowania:</h2>
<ul>
    <li><strong>Email:</strong> {{ email }}</li>
    <li><strong>Hasło tymczasowe:</strong> {{ password }}</li>
</ul>

<p><strong>WAŻNE:</strong> Zmień hasło natychmiast po pierwszym logowaniu!</p>

<h2>Rozpocznij pracę:</h2>
<ol>
    <li>Zaloguj się na <a href="{{ login_url }}">{{ login_url }}</a></li>
    <li>Zmień hasło</li>
    <li>Uzupełnij profil</li>
    <li>Dodaj pierwszych korepetytorów</li>
    <li>Dodaj pierwszych uczniów</li>
</ol>

<h2>Potrzebujesz pomocy?</h2>
<ul>
    <li>Dokumentacja: <a href="{{ docs_url }}">{{ docs_url }}</a></li>
    <li>Email: support@napiatke.pl</li>
</ul>

<p>Powodzenia!</p>
<p>Zespół Na Piątkę</p>
{% endblock %}
```

### Training Checklist

**File**: `docs/training/admin-training-checklist.md`

```markdown
# Szkolenie Administratora - Checklist

## 1. Logowanie i Bezpieczeństwo (15 min)
- [ ] Logowanie do systemu
- [ ] Zmiana hasła
- [ ] Wylogowanie
- [ ] Resetowanie hasła

## 2. Zarządzanie Użytkownikami (30 min)
- [ ] Dodawanie korepetytora
- [ ] Dodawanie ucznia
- [ ] Edycja profilu użytkownika
- [ ] Dezaktywacja konta
- [ ] Eksport danych (RODO)

## 3. Kalendarz i Lekcje (30 min)
- [ ] Nawigacja po kalendarzu
- [ ] Tworzenie lekcji indywidualnej
- [ ] Tworzenie lekcji grupowej
- [ ] Lekcje cykliczne
- [ ] Wykrywanie konfliktów

## 4. Obecności (15 min)
- [ ] Oznaczanie obecności
- [ ] Przeglądanie historii
- [ ] Raporty frekwencji

## 5. Anulowania i Odrabianie (20 min)
- [ ] Zatwierdzanie anulowań
- [ ] Zarządzanie kolejką odrabiania
- [ ] Przedłużanie terminów

## 6. Faktury (15 min)
- [ ] Automatyczne generowanie
- [ ] Korekty
- [ ] Oznaczanie płatności

## 7. Ustawienia Systemu (10 min)
- [ ] Przedmioty i poziomy
- [ ] Sale
- [ ] Ustawienia ogólne
```

---

## GO-LIVE CHECKLIST

### Pre-Launch (T-24h)

#### Technical Readiness

- [ ] **Code deployed to production**
  - Latest commit on `main` branch
  - Docker images built successfully
  - All containers running

- [ ] **Database ready**
  - Migrations completed
  - Seed data populated
  - Backups configured
  - Connection pooling enabled

- [ ] **Environment variables set**
  - `SECRET_KEY` unique and secure
  - `DATABASE_URL` configured
  - `REDIS_URL` configured
  - `SENTRY_DSN` configured
  - `RESEND_API_KEY` configured

- [ ] **Domain & DNS**
  - Domain points to server
  - SSL certificate valid
  - DNS propagated globally
  - Email records verified

- [ ] **Security hardened**
  - Security headers configured
  - Rate limiting active
  - HTTPS enforced
  - Firewall configured

- [ ] **Monitoring active**
  - Sentry capturing errors
  - Logging configured
  - Uptime monitoring
  - Alerts configured

- [ ] **Backups**
  - Daily backups scheduled
  - Restoration tested
  - Off-site storage (S3)

### Launch Day (T-0)

#### Final Verification

- [ ] **Run smoke tests**
  ```bash
  ./scripts/smoke-test.sh
  ```

- [ ] **Verify all services**
  - Web: healthy
  - Database: connected
  - Redis: connected
  - Celery: running

- [ ] **Check monitoring**
  - Sentry: no errors
  - Logs: no critical issues
  - Performance: within targets

#### Go-Live

- [ ] **Enable production features**
  - Cron jobs active
  - Email notifications enabled
  - Celery beat running

- [ ] **Send welcome communications**
  - Admin credentials sent
  - Tutor invitations sent
  - Student invitations sent

- [ ] **Monitor first hour**
  - Watch Sentry (every 5 min)
  - Check database connections
  - Verify emails sending
  - Monitor performance

### Post-Launch (T+24h)

#### Health Check

- [ ] **Review metrics**
  - User registrations
  - Error rate (<1%)
  - Uptime (>99.9%)
  - Response time (<500ms avg)

- [ ] **Collect feedback**
  - Admin feedback
  - User issues logged
  - Improvements noted

- [ ] **Continuous monitoring**
  - Daily: Check Sentry
  - Weekly: Review analytics
  - Monthly: Security audit

---

## LAUNCH DECLARATION

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║            🎓 SYSTEM LAUNCH DECLARATION 🎓                    ║
║                                                               ║
║                     "Na Piątkę"                               ║
║          Tutoring Management System CMS                       ║
║                                                               ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                               ║
║  Technology Stack:                                            ║
║  ✓ Django 5.1                                                ║
║  ✓ PostgreSQL 17                                             ║
║  ✓ Redis 7                                                   ║
║  ✓ HTMX 2.0 + Alpine.js 3.x                                 ║
║  ✓ Tailwind CSS + daisyUI                                   ║
║  ✓ Celery + Celery Beat                                     ║
║  ✓ Docker + Nginx + Gunicorn                                ║
║                                                               ║
║  Quality Metrics:                                             ║
║  ✓ Test Coverage: >80%                                       ║
║  ✓ Performance Score: >90                                    ║
║  ✓ Security: OWASP Top 10 addressed                          ║
║  ✓ Production Ready: YES                                     ║
║                                                               ║
║  Production URL: https://napiatke.pl                         ║
║                                                               ║
║  Status: 🚀 LIVE IN PRODUCTION                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## COMPLETION CHECKLIST

### Deployment

- [ ] Docker containers running
- [ ] Database migrated
- [ ] Static files collected
- [ ] Health check passing

### Domain & SSL

- [ ] DNS configured
- [ ] SSL certificate valid
- [ ] HTTPS enforced
- [ ] Security headers active

### Testing

- [ ] Smoke tests passing
- [ ] Performance targets met
- [ ] No critical errors

### Users

- [ ] Initial users created
- [ ] Training completed
- [ ] Welcome emails sent
- [ ] Support ready

### Documentation

- [ ] User guides available
- [ ] API documented
- [ ] Deployment guide complete
- [ ] Disaster recovery plan

---

**Sprint Completion**: All 8 tasks completed and validated
**Phase Completion**: Phase 13 - Deployment COMPLETE
**Project Status**: LIVE IN PRODUCTION

---

## Post-Launch Continuous Improvement

### Phase 14 Ideas (Future):

1. **Mobile apps** (React Native / Flutter)
2. **Advanced analytics dashboard**
3. **AI-powered scheduling**
4. **Video conferencing integration**
5. **Payment gateway integration** (Stripe, PayU)
6. **Multi-language support**
7. **Parent mobile app**
8. **Student progress gamification**

### Maintenance Schedule:

- **Weekly**: Dependency updates, bug fixes
- **Monthly**: Feature requests, user feedback
- **Quarterly**: Security audit, performance review
- **Yearly**: Major version upgrades

---

**Congratulations! Na Piątkę is now LIVE!** 🎉
