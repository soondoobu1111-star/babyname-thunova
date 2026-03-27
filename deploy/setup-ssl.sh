#!/bin/bash
# DNS 전파 확인 후 SSL 발급 + nginx HTTPS 전환
# EC2에서 직접 실행: bash /home/ubuntu/babyname/deploy/setup-ssl.sh

DOMAIN="babyname.kfortunewave.com"
EC2_IP="65.2.153.115"

echo "=== DNS 전파 확인 ==="
RESOLVED=$(dig +short $DOMAIN 2>/dev/null)
if [ "$RESOLVED" != "$EC2_IP" ]; then
    echo "❌ DNS 미전파: $DOMAIN → $RESOLVED (기대값: $EC2_IP)"
    echo "Route53에서 A 레코드를 추가하고 다시 실행하세요."
    exit 1
fi
echo "✅ DNS 전파 완료: $DOMAIN → $EC2_IP"

echo ""
echo "=== SSL 발급 ==="
/snap/bin/certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m thunova0318@gmail.com

echo ""
echo "=== nginx 재시작 ==="
sudo systemctl reload nginx

echo ""
echo "=== 완료 ==="
echo "https://$DOMAIN 접속 가능합니다."
