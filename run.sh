#!/bin/bash

echo "🚀 Ziyofat-day loyihasini ishga tushirish..."

# Backendni orqa fonda (background) yurg'izish
echo "1️⃣ Backend server ishga tushirilmoqda (localhost:8000)..."
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "2️⃣ Frontend server ishga tushirilmoqda (localhost:3000)..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo "✅ Barchasi tayyor!"
echo "🌐 Brauzerda quyidagi manzilni oching: http://127.0.0.1:3000"
echo "To'xtatish uchun CTRL+C bosing."

# Dasturlar ishlashini ushlab turamiz
wait
