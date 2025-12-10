#!/bin/bash
# Generate self-signed SSL certificate for development

mkdir -p certs

openssl req -x509 -newkey rsa:4096 -nodes \
  -out certs/cert.pem \
  -keyout certs/key.pem \
  -days 365 \
  -subj "/C=VN/ST=HoChiMinh/L=HoChiMinh/O=TMDT/OU=Dev/CN=localhost"

echo "✅ SSL certificates generated in ./certs/"
echo "   - cert.pem (certificate)"
echo "   - key.pem (private key)"
echo ""
echo "To run with HTTPS:"
echo "  python main_https.py"
