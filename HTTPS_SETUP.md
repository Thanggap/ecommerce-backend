# 🔐 HTTPS Development Setup

Quick guide để chạy backend với HTTPS trong môi trường development.

## Step 1: Generate SSL Certificate

```bash
cd backend
./generate_cert.sh
```

Output:
```
✅ SSL certificates generated in ./certs/
   - cert.pem (certificate)
   - key.pem (private key)

To run with HTTPS:
  python main_https.py
```

## Step 2: Run Backend with HTTPS

```bash
python main_https.py
```

Server chạy tại: **https://localhost:8000**

## Step 3: Accept Self-Signed Certificate

Khi mở browser, bạn sẽ thấy warning:

```
Your connection is not private
NET::ERR_CERT_AUTHORITY_INVALID
```

**Fix:**
1. Click **Advanced**
2. Click **Proceed to localhost (unsafe)**

Certificate sẽ được browser remember cho session.

## Step 4: Update Frontend API URL (Optional)

Nếu frontend cần gọi HTTPS backend:

```typescript
// frontend/src/constants.ts
export const BACKEND_URL = "https://localhost:8000/api";
```

⚠️ **CORS Note:** HTTPS backend chỉ accept requests từ HTTPS frontend (hoặc localhost HTTP)

## Testing HTTPS

### Verify SSL Connection:
```bash
curl -k https://localhost:8000/api/
```

Output:
```json
{"message": "Hello, world!"}
```

### Check Security Headers:
```bash
curl -Ik https://localhost:8000/api/
```

Expect to see:
```
HTTP/1.1 200 OK
strict-transport-security: max-age=31536000; includeSubDomains; preload
x-content-type-options: nosniff
x-frame-options: DENY
x-xss-protection: 1; mode=block
```

## Certificate Details

Self-signed certificate info:
- **Valid for:** 365 days
- **Algorithm:** RSA 4096-bit
- **Subject:** CN=localhost, O=TMDT, C=VN
- **Type:** X.509

## Switching Back to HTTP

Chỉ cần chạy:
```bash
python main.py
```

Server sẽ chạy HTTP tại: http://localhost:8000

## Production Setup

For production, replace self-signed cert với Let's Encrypt:

```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Update uvicorn
uvicorn app.app:app \
  --ssl-keyfile=/etc/letsencrypt/live/yourdomain.com/privkey.pem \
  --ssl-certfile=/etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

## Troubleshooting

### Certificate không được trust?
- Normal cho self-signed certs
- Browser sẽ show warning - click "Proceed anyway"
- Production dùng Let's Encrypt sẽ tự động trusted

### CORS errors với HTTPS?
Check `app/app.py` CORS config:
```python
allow_origins=[
    "https://localhost:3000",  # Add HTTPS origin
]
```

### Port 8000 already in use?
```bash
# Kill process
lsof -ti:8000 | xargs kill -9

# Hoặc dùng port khác
uvicorn app.app:app --port 8443 --ssl-keyfile=...
```
