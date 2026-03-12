# FREE11 Production Deployment Guide
## Deploying free11.com on a VPS (Ubuntu 22.04 LTS)

---

## 1. System Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl git nginx certbot python3-certbot-nginx \
  python3 python3-pip python3-venv nodejs npm mongodb-org redis-server

# Install Node.js 20 (for React build)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install yarn
npm install -g yarn

# Verify
node --version   # Should be 20+
python3 --version  # Should be 3.10+
```

---

## 2. Clone & Set Up the Application

```bash
# Create app user
sudo useradd -m -s /bin/bash free11
sudo su - free11

# Clone repository
git clone https://github.com/YOUR_ORG/free11.git /home/free11/app
cd /home/free11/app
```

---

## 3. Backend Setup (FastAPI)

```bash
cd /home/free11/app/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `/home/free11/app/backend/.env`:
```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=free11

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-jwt-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Production API Keys (replace stubs)
RAZORPAY_KEY_ID=rzp_live_XXXX
RAZORPAY_KEY_SECRET=XXXX
RESEND_API_KEY=re_XXXX
FIREBASE_SERVICE_ACCOUNT_PATH=/home/free11/app/backend/firebase-service-account.json
XOXODAY_API_KEY=XXXX
ENTITY_SPORTS_KEY=your-entity-sports-key
SENTRY_DSN=https://your-sentry-dsn@sentry.io/xxx

# App Config
ALLOWED_ORIGINS=https://free11.com,https://www.free11.com
ENVIRONMENT=production
APP_NAME=FREE11
```

---

## 4. Frontend Build

```bash
cd /home/free11/app/frontend

# Create production .env
cat > .env.production << 'EOF'
REACT_APP_BACKEND_URL=https://free11.com
REACT_APP_APP_ENV=production
EOF

# Install dependencies
yarn install

# Build for production
yarn build

# Output is in /home/free11/app/frontend/build/
```

---

## 5. Systemd Services

### Backend Service

Create `/etc/systemd/system/free11-backend.service`:
```ini
[Unit]
Description=FREE11 FastAPI Backend
After=network.target mongod.service redis.service

[Service]
Type=exec
User=free11
WorkingDirectory=/home/free11/app/backend
Environment=PATH=/home/free11/app/backend/venv/bin
ExecStart=/home/free11/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable free11-backend
sudo systemctl start free11-backend
sudo systemctl status free11-backend
```

---

## 6. Nginx Configuration

Create `/etc/nginx/sites-available/free11.com`:
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name free11.com www.free11.com;
    return 301 https://$server_name$request_uri;
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    server_name free11.com www.free11.com;

    # SSL (managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/free11.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/free11.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Root - Serve React build
    root /home/free11/app/frontend/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml application/json application/javascript application/xml+rss text/javascript image/svg+xml;

    # API proxy to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
        client_max_body_size 50M;
    }

    # PWA Service Worker - no cache
    location /service-worker.js {
        root /home/free11/app/frontend/build;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }

    # PWA Manifest - short cache
    location /manifest.json {
        root /home/free11/app/frontend/build;
        add_header Cache-Control "no-cache";
        add_header Access-Control-Allow-Origin *;
    }

    # .well-known for TWA/Digital Asset Links
    location /.well-known/ {
        root /home/free11/app/frontend/build;
        add_header Access-Control-Allow-Origin *;
        add_header Cache-Control "no-cache";
    }

    # Static assets - aggressive caching
    location /static/ {
        root /home/free11/app/frontend/build;
        add_header Cache-Control "public, max-age=31536000, immutable";
        expires 1y;
    }

    # All other routes → React app (SPA routing)
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/free11.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. SSL Setup with Let's Encrypt

```bash
# Issue certificate (before setting up nginx SSL block)
sudo certbot --nginx -d free11.com -d www.free11.com \
  --non-interactive --agree-tos -m admin@free11.com

# Verify auto-renewal
sudo certbot renew --dry-run

# Crontab for renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 8. MongoDB Setup

```bash
# Start MongoDB
sudo systemctl enable mongod
sudo systemctl start mongod

# Create database user
mongosh << 'EOF'
use free11
db.createUser({
  user: "free11app",
  pwd: "your-strong-password",
  roles: [{ role: "readWrite", db: "free11" }]
})
EOF

# Update MONGO_URL in backend .env to use auth:
# MONGO_URL=mongodb://free11app:password@localhost:27017/free11
```

---

## 9. Redis Setup

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Configure Redis password (optional but recommended)
sudo nano /etc/redis/redis.conf
# Uncomment and set: requirepass your-redis-password

sudo systemctl restart redis-server
```

---

## 10. PWA Manifest Verification

Verify `/home/free11/app/frontend/build/manifest.json` contains:
```json
{
  "name": "FREE11 - Social Entertainment Sports",
  "short_name": "FREE11",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0a0e17",
  "theme_color": "#f59e0b",
  "icons": [
    { "src": "/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### Install on Android Chrome:
1. Navigate to https://free11.com in Chrome
2. Tap the "Add to Home Screen" banner or use menu → "Install App"
3. The app launches in standalone mode (no browser chrome)

### Install on iOS Safari:
1. Navigate to https://free11.com in Safari
2. Tap the Share button (square with arrow)
3. Tap "Add to Home Screen"
4. Note: iOS PWAs don't support push notifications fully

### Install on Desktop (Chrome/Edge):
1. Navigate to https://free11.com
2. Click the install icon in the address bar (or menu → "Install FREE11")

---

## 11. Service Worker Verification

```bash
# Check service worker is accessible
curl -I https://free11.com/service-worker.js
# Should return: Cache-Control: no-cache, no-store, must-revalidate

# Check manifest
curl -I https://free11.com/manifest.json
# Should return: Content-Type: application/json
```

---

## 12. .well-known/assetlinks.json (for Android TWA)

Create `/home/free11/app/frontend/public/.well-known/assetlinks.json`:
```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.free11.app",
    "sha256_cert_fingerprints": [
      "REPLACE_WITH_YOUR_APK_SHA256_FINGERPRINT"
    ]
  }
}]
```

After building the APK in Android Studio, get the SHA-256 fingerprint:
```bash
keytool -list -v -keystore free11.keystore -alias free11key
# Copy the SHA256 fingerprint from output
```

---

## 13. Production Deployment Checklist

- [ ] Domain DNS pointing to VPS IP
- [ ] SSL certificate issued and auto-renewing
- [ ] Nginx config tested (`nginx -t`)
- [ ] Backend running on port 8001
- [ ] MongoDB accessible and authenticated
- [ ] Redis running
- [ ] All production .env keys filled (Razorpay, Resend, Firebase, Xoxoday)
- [ ] `assetlinks.json` deployed at `/.well-known/assetlinks.json`
- [ ] Manifest.json accessible at `/manifest.json`
- [ ] Service worker served with no-cache headers
- [ ] PWA installable on Android Chrome (check Lighthouse audit)
- [ ] Sentry error tracking active

---

## 14. Monitoring

```bash
# Check backend logs
journalctl -u free11-backend -f

# Check nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check MongoDB
mongosh free11 --eval "db.users.countDocuments()"

# Nginx status
sudo nginx -t && sudo systemctl status nginx
```

---

## 15. Updating the App

```bash
cd /home/free11/app

# Pull latest
git pull origin main

# Backend (if dependencies changed)
cd backend && source venv/bin/activate && pip install -r requirements.txt

# Frontend rebuild
cd ../frontend
yarn install
REACT_APP_BACKEND_URL=https://free11.com yarn build

# Restart backend
sudo systemctl restart free11-backend

# Reload nginx (if config changed)
sudo systemctl reload nginx
```
