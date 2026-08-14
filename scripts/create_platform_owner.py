"""
Platforma egasi (barcha restoranlar/obunalarni boshqaradigan) hisobini yaratadi.
Bu hisob hech qaysi restoranga tegishli emas (restaurant_id = NULL) va
/admin panelida faqat shunga ruxsat etilgan Restaurant bo'limini ko'radi.

Ishlatish:
    uv run python scripts/create_platform_owner.py <username> <password>
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models import User
from app.utils import hash_password


def main():
    if len(sys.argv) != 3:
        print("Ishlatish: uv run python scripts/create_platform_owner.py <username> <password>")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]

    db = SessionLocal()
    try:
        existing = (
            db.query(User)
            .filter(User.username == username, User.restaurant_id.is_(None))
            .first()
        )
        if existing:
            print(f"'{username}' nomli platforma egasi allaqachon mavjud (id={existing.id}).")
            return

        user = User(
            restaurant_id=None,
            username=username,
            password_hash=hash_password(password),
            role="platform_owner",
            is_admin=False,
            is_platform_owner=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Platforma egasi yaratildi: id={user.id}, username={user.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
