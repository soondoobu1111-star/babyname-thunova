#!/bin/bash
# 써노바 작명연구소 EC2 배포 스크립트
# 실행: ./deploy/deploy.sh
set -e

EC2="ubuntu@65.2.153.115"
KEY="$HOME/Downloads/ksaju-key.pem"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="/home/ubuntu/babyname"

echo "=== 1. EC2에 파일 전송 ==="
ssh -i "$KEY" $EC2 "mkdir -p $DEST/saju $DEST/naming $DEST/pdf $DEST/orders $DEST/deploy"

rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude 'orders/*.db' --exclude 'orders/*.pdf' \
  -e "ssh -i $KEY" \
  "$SRC/app.py" \
  "$SRC/database.py" \
  "$SRC/requirements.txt" \
  "$SRC/saju/" \
  "$SRC/naming/" \
  "$SRC/pdf/" \
  "$EC2:$DEST/"

echo "=== 2. EC2에서 패키지 설치 ==="
ssh -i "$KEY" $EC2 "cd $DEST && pip3 install -r requirements.txt --quiet"

echo "=== 3. systemd 서비스 등록 ==="
scp -i "$KEY" "$SRC/deploy/babyname.service" $EC2:/tmp/babyname.service
ssh -i "$KEY" $EC2 "sudo mv /tmp/babyname.service /etc/systemd/system/babyname.service && sudo systemctl daemon-reload && sudo systemctl enable babyname && sudo systemctl restart babyname"

echo "=== 4. nginx 설정 ==="
scp -i "$KEY" "$SRC/deploy/babyname-nginx.conf" $EC2:/tmp/babyname-nginx.conf
ssh -i "$KEY" $EC2 "sudo mv /tmp/babyname-nginx.conf /etc/nginx/sites-available/babyname-kfortunewave && sudo ln -sf /etc/nginx/sites-available/babyname-kfortunewave /etc/nginx/sites-enabled/babyname-kfortunewave && sudo nginx -t && sudo systemctl reload nginx"

echo ""
echo "=== 5. SSL 발급 (최초 1회만) ==="
echo "아래 명령어를 EC2에서 직접 실행하세요:"
echo "  sudo certbot --nginx -d babyname.kfortunewave.com"

echo ""
echo "=== 6. .env 파일 설정 ==="
echo "EC2에서 직접 실행:"
echo "  nano $DEST/.env"
echo ""
echo "내용:"
echo "  GEMINI_API_KEY=새로받은키"
echo ""

echo "=== 배포 완료 ==="
ssh -i "$KEY" $EC2 "sudo systemctl status babyname --no-pager | head -10"
