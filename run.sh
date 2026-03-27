#!/bin/bash
# 써노바 작명연구소 — 로컬 서버 실행
cd "$(dirname "$0")"
echo "🏮 써노바 작명연구소 시작..."
echo "📌 http://localhost:8501 에서 접속하세요"
python3 -m streamlit run app.py --server.port 8501 --server.headless false
