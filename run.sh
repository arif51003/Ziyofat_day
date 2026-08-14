#!/bin/bash

echo "🚀 Ziyofat-day loyihasini ishga tushirish..."

# Backend frontend (statik fayllar + SPA fallback) bilan birga bitta portda ishlaydi
echo "1️⃣ Server ishga tushirilmoqda (localhost:8000)..."
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "✅ Barchasi tayyor!"
echo "🌐 Brauzerda quyidagi manzilni oching: http://127.0.0.1:8000"
echo "To'xtatish uchun CTRL+C bosing."

# Dasturlar ishlashini ushlab turamiz
wait
