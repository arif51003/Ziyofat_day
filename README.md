# Ziyofat Day

Kichik va o'rta restoran/kafelar uchun **bulutga asoslangan boshqaruv tizimi (Restaurant POS)**.
Stol, buyurtma, oshxona ish jarayoni, kassa va ombor nazoratini bitta tizimda birlashtiradi.

Backend: **FastAPI + PostgreSQL + SQLAlchemy 2.0**
Frontend: **Vanilla JS SPA** (build vositasisiz, to'g'ridan-to'g'ri brauzerda ishlaydi)
Admin panel: **Starlette-Admin** (`/admin`)

---

## Mundarija

- [Muammo va yechim](#muammo-va-yechim)
- [Asosiy imkoniyatlar](#asosiy-imkoniyatlar)
- [Arxitektura](#arxitektura)
- [Foydalanuvchi rollari](#foydalanuvchi-rollari)
- [Loyihani ishga tushirish](#loyihani-ishga-tushirish)
- [Muhit o'zgaruvchilari (.env)](#muhit-ozgaruvchilari-env)
- [Ma'lumotlar bazasi va migratsiyalar](#malumotlar-bazasi-va-migratsiyalar)
- [Demo ma'lumotlar bilan to'ldirish (seed)](#demo-malumotlar-bilan-toldirish-seed)
- [Birinchi admin yaratish](#birinchi-admin-yaratish)
- [API endpointlar](#api-endpointlar)
- [Buyurtma workflow](#buyurtma-workflow)
- [Loyiha tuzilishi](#loyiha-tuzilishi)
- [Ishlab chiqish (dev) buyruqlari](#ishlab-chiqish-dev-buyruqlari)
- [Xavfsizlik eslatmalari](#xavfsizlik-eslatmalari)

---

## Muammo va yechim

O'zbekistondagi ko'plab restoran va kafelarda buyurtmalar qog'ozda yoki og'zaki uzatiladi. Bu quyidagilarga olib keladi:

- Buyurtma chalkashuvi va yo'qolishi
- Kassada nazorat yo'qligi, hisob-kitobdagi xatolar
- Ombordagi mahsulot sarfini kuzatib bo'lmasligi
- Kim nima qilganini bilib bo'lmasligi (audit yo'qligi)

**Ziyofat Day** — ofitsiant stolni ochishidan, oshxona tayyorlashidan, kassa to'lovni yopishigacha bo'lgan butun jarayonni raqamlashtiradi va har bir harakatni tizimda qayd etadi.

## Asosiy imkoniyatlar

- 🍽️ **Stol boshqaruvi** — bo'sh / band / rezerv holatlari
- 🧾 **Buyurtma qabul qilish** — menyu, variantlar (o'lcham/tur), izohlar
- 👨‍🍳 **Oshxona workflow** — yangi → tayyorlanmoqda → tayyor → mijozga berildi
- 📦 **Ombor nazorati** — retsept asosida ingredientlar avtomatik ayiriladi, yetarli bo'lmasa buyurtma yuborilmaydi
- 💳 **Kassa va to'lov** — qisman to'lov, aralash to'lov usuli, chek chiqarish
- 🔐 **Rolga asoslangan kirish** — JWT token, har bir rol faqat o'ziga tegishli amallarni bajaradi
- 🖥️ **Admin panel** — menyu, xodimlar, stollar, hisobotlarni boshqarish (Starlette-Admin)
- 📊 **To'liq kuzatuv** — har bir order-item bosqichi vaqti bilan saqlanadi (`sent_at`, `ready_at`, `served_at`)

## Arxitektura

```
┌─────────────┐      HTTP/JSON       ┌───────────────────┐
│  Frontend   │ ───────────────────▶ │   FastAPI backend  │
│  (SPA, JS)  │ ◀─────────────────── │   app/             │
└─────────────┘     JWT Bearer        └─────────┬──────────┘
                                                 │
                                     ┌───────────┼────────────┐
                                     ▼           ▼            ▼
                               PostgreSQL   Starlette-Admin  media_uploads/
                               (SQLAlchemy)   (/admin)        (rasm fayllar)
```

- **Autentifikatsiya**: `POST /auth/login/` orqali `access_token` va `refresh_token` (JWT) olinadi. Har bir so'rov `Authorization: Bearer <token>` headeri bilan yuboriladi.
- **Ro'yxatdan o'tkazish**: yangi xodim faqat admin tomonidan (`/auth/user-create`, admin tokeni bilan) yaratiladi — mijozlar ro'yxatdan o'tmaydi.
- **Frontend** backenddan mustaqil, `frontend/js/api.js` ichidagi `API_BASE` orqali backend manziliga ulanadi.

## Foydalanuvchi rollari

| Rol | Imkoniyatlari |
|---|---|
| **Admin** | Xodimlarni yaratadi, menyu/stol/ingredient boshqaradi, barcha hisobotlarni ko'radi (`/admin` paneli orqali) |
| **Ofitsiant (waiter)** | Login/logout, profilini ko'rish/tahrirlash, stol ochish/band qilish, buyurtma yozish va oshxonaga yuborish, tayyor taomni mijozga berilgan deb belgilash, o'zi ochgan buyurtmalarni ko'rish va qidirish |
| **Oshxona (kitchen)** | O'ziga tegishli stansiya (station) bo'yicha joriy buyurtmalarni ko'radi, tayyorlashni boshlaydi va tayyor deb belgilaydi |
| **Kassir (cashier)** | Barcha to'lanmagan/to'langan buyurtmalarni ko'radi, to'lov qabul qiladi, buyurtmani yopadi, chek chiqaradi |
| **Mijoz** | Login qilmaydi — faqat frontend orqali ochiq menyuni ko'radi |

Har bir muhim amal (buyurtma ochish, yopish, to'lov, foydalanuvchi yaratish va h.k.) `audit_log` jadvaliga yoziladi.

## Loyihani ishga tushirish

### Talablar

- Python **3.12+**
- PostgreSQL (mahalliy yoki masofaviy server)
- [uv](https://docs.astral.sh/uv/) paket menejeri (tavsiya etiladi) yoki `pip`

### 1. Repositoryni klonlash va bog'liqliklarni o'rnatish

```bash
git clone <repo-url> ziyofat-day
cd ziyofat-day
uv sync
```

`uv` yo'q bo'lsa, oddiy `venv` + `pip` bilan ham o'rnatish mumkin:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. `.env` faylini sozlash

```bash
cp .env.exam .env
```

`.env` faylini o'zingizning ma'lumotlaringiz bilan to'ldiring (pastdagi bo'limga qarang).

### 3. Ma'lumotlar bazasini tayyorlash

```bash
# PostgreSQLda bo'sh baza yarating (agar mavjud bo'lmasa)
createdb ziyofat_day

# Migratsiyalarni qo'llash
uv run alembic upgrade head
```

### 4. Serverni ishga tushirish

```bash
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Yoki backend va frontendni birgalikda ishga tushirish uchun:

```bash
./run.sh
```

Bu skript backendni `http://127.0.0.1:8000` da, frontendni esa (static server orqali) `http://127.0.0.1:3000` da ko'taradi.

> **Eslatma:** Agar frontend va backend bir xil portda (`8000`) ishlatilsa, `app/main.py` allaqachon `frontend/` papkasini SPA sifatida serve qilishga sozlangan — alohida frontend serverga ehtiyoj qolmaydi.

Ishga tushgach:
- API hujjatlari: `http://127.0.0.1:8000/docs`
- Admin panel: `http://127.0.0.1:8000/admin`

## Muhit o'zgaruvchilari (.env)

| O'zgaruvchi | Tavsif | Misol |
|---|---|---|
| `PROJECT_NAME` | Loyiha nomi | `Ziyofat Day` |
| `DEBUG` | Debug rejimi | `true` / `false` |
| `SECRET_KEY` | JWT imzolash uchun maxfiy kalit (production'da uzun, tasodifiy qiymat bo'lishi shart) | `openssl rand -hex 32` bilan generatsiya qiling |
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` / `DB_NAME` | PostgreSQL ulanish ma'lumotlari | `postgres` / `***` / `localhost` / `5432` / `ziyofat_day` |

`app/config.py` da qo'shimcha standart qiymatlar mavjud: `ACCESS_TOKEN_EXPIRE_MINUTES=30`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `ALGORITHM=HS256`.

**Muhim:** `.env` fayli hech qachon repositoryga qo'shilmasin (`.gitignore` da allaqachon istisno qilingan).

## Ma'lumotlar bazasi va migratsiyalar

Loyiha **Alembic** orqali migratsiyalarni boshqaradi.

```bash
# Joriy holatga yangilash
uv run alembic upgrade head

# Model o'zgarishidan keyin yangi migratsiya yaratish
uv run alembic revision --autogenerate -m "tavsif"

# Bir qadam orqaga qaytarish
uv run alembic downgrade -1
```

Asosiy jadvallar: `users`, `dining_table`, `menu_category`, `menu_item`, `menu_item_variant`, `orders`, `order_item`, `payment`, `audit_log`, `ingredients`, `menu_ingredient`, `ingredient_stock`, `stock_movements`, `media`.

## Demo ma'lumotlar bilan to'ldirish (seed)

Tizimni bo'sh bazada sinab ko'rish uchun `scripts/seed_data.py` skripti barcha jadvallarga real restoranga mos, bir-biriga to'liq bog'langan namuna ma'lumotlarni joylaydi:

```bash
uv run python scripts/seed_data.py --yes
```

> **DIQQAT:** bu skript ishga tushirilgan jadvallardagi (`users`, `orders`, `menu_item` va h.k.) **barcha mavjud ma'lumotlarni o'chirib**, o'rniga demo ma'lumotlarni yozadi (`TRUNCATE ... CASCADE`). Production bazada hech qachon ishlatmang. `--yes` bermasangiz, skript tasdiqlashni so'raydi.

Yaratiladigan demo ma'lumotlar:

| Model | Miqdor | Izoh |
|---|---|---|
| Foydalanuvchilar | 8 ta | 1 admin, 3 waiter, 2 kitchen, 2 cashier. Parol: `<username>123` (masalan `admin` / `admin123`) |
| Stollar | 10 ta | turli sig'imda, 2 tasi band, 1 tasi rezerv holatida |
| Menyu kategoriyalari | 6 ta | Salatlar, Sho'rvalar, Issiq taomlar, Fast-food, Ichimliklar, Shirinliklar |
| Menyu bandlari | 24 ta | har biri narx, stansiya va **to'liq retsept** bilan |
| Ingredientlar + ombor | 18 ta | har biriga boshlang'ich ombor qoldig'i (`ingredient_stock`) bilan |
| Variantlar | 6 ta | ba'zi taomlar uchun (katta porsiya, qo'shimcha shish va h.k.) |
| Namuna buyurtmalar | 3 ta | 1 yopilgan/to'langan, 1 oshxonada tayyorlanayotgan, 1 hali ochiq |
| Audit log | 3 ta | namuna yozuvlar |

## Birinchi admin yaratish

Seed skripti ishlatilganda `admin` foydalanuvchisi avtomatik yaratiladi. Agar seed skriptisiz, bo'sh bazada faqat admin kerak bo'lsa, quyidagicha to'g'ridan-to'g'ri Python orqali yaratish mumkin (`/auth/user-create` endpointi faqat mavjud admin tokeni bilan ishlaydi):

```bash
uv run python -c "
from app.database import SessionLocal
from app.models import User
from app.utils import hash_password

db = SessionLocal()
admin = User(
    username='admin',
    password_hash=hash_password('kuchli-parol'),
    role='admin',
    is_admin=True,
)
db.add(admin)
db.commit()
db.close()
print('Admin yaratildi:', admin.username)
"
```

Shundan so'ng `admin` bilan `/admin` panelidan yoki `/auth/login/` orqali kirib, boshqa xodimlarni (`waiter`, `kitchen`, `cashier`) yarata olasiz.

## API endpointlar

Barcha endpointlar `/docs` (Swagger UI) orqali interaktiv ko'rinadi. Qisqacha xarita:

### Auth — `/auth`
| Metod | Yo'l | Tavsif | Ruxsat |
|---|---|---|---|
| POST | `/auth/login/` | Login, JWT token olish | Ochiq |
| POST | `/auth/refresh/` | Access tokenni yangilash | Refresh token |
| POST | `/auth/logout` | Chiqish (token qora ro'yxatga) | Login qilingan |
| POST | `/auth/user-create` | Yangi xodim yaratish | Faqat Admin |

### User — `/user`
| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/user/profile/` | O'z profilini ko'rish |
| PATCH | `/user/profile/update` | Profilni (ism, avatar) tahrirlash |

### Waiter — `/waiter`
| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/waiter/menu` | To'liq menyuni olish |
| GET | `/waiter/tables/free` | Bo'sh stollar ro'yxati |
| POST | `/waiter/orders/open` | Stol uchun yangi buyurtma ochish |
| GET | `/waiter/orders/my-active` | O'zining aktiv buyurtmalari |
| GET | `/waiter/orders/{id}` | Buyurtma tafsiloti |
| POST | `/waiter/orders/{id}/items` | Buyurtmaga item qo'shish |
| PATCH | `/waiter/orders/{id}/items/{item_id}` | Item miqdori/izohini o'zgartirish |
| DELETE | `/waiter/orders/{id}/items/{item_id}` | Itemni o'chirish |
| POST | `/waiter/orders/{id}/submit` | Buyurtmani oshxonaga yuborish (ombordan ayiriladi) |
| POST | `/waiter/orders/{id}/items/{item_id}/serve` | Tayyor taomni mijozga berilgan deb belgilash |
| GET | `/waiter/orders/search?q=` | Buyurtmalarni qidirish |

### Kitchen — `/kitchen`
| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/kitchen/order-items/queue` | Tayyorlanishi kerak bo'lgan itemlar navbati |
| GET | `/kitchen/orders/{id}` | Buyurtma bo'yicha oshxona ko'rinishi |
| POST | `/kitchen/order-items/{id}/start` | Tayyorlashni boshlash |
| POST | `/kitchen/order-items/{id}/ready` | Tayyor deb belgilash |

### Cashier — `/cashier`
| Metod | Yo'l | Tavsif |
|---|---|---|
| GET | `/cashier/orders/unpaid` | To'lanmagan buyurtmalar |
| GET | `/cashier/orders/paid` | To'langan (yopilgan) buyurtmalar |
| GET | `/cashier/orders/{id}/summary` | Buyurtma bo'yicha to'liq hisob |
| POST | `/cashier/orders/{id}/pay` | To'lov qabul qilish (qisman/to'liq) |
| POST | `/cashier/orders/{id}/close` | Buyurtmani yopish (to'liq to'langanda) |

## Buyurtma workflow

```
Stol bo'sh ──▶ Ofitsiant stol ochadi (open) ──▶ Itemlar qo'shiladi (new)
                                                          │
                                                 Oshxonaga yuboriladi (submit)
                                                 → ombordan ingredient ayiriladi
                                                          │
                                                          ▼
                                          Order: submitted  |  Item: sent
                                                          │
                                        Oshxona: tayyorlashni boshlaydi (preparing)
                                                          │
                                        Oshxona: tayyor deb belgilaydi (ready)
                                                          │
                                     Ofitsiant: mijozga beradi (served)
                                                          │
                                     Kassir: to'lovni qabul qiladi (pay)
                                                          │
                                     Kassir: buyurtmani yopadi (close)
                                                          │
                                                          ▼
                                                  Stol yana bo'sh bo'ladi
```

Bitta buyurtmaga bir nechta marta item qo'shish mumkin — har safar `submit` chaqirilganda faqat `new` holatdagi itemlar oshxonaga yuboriladi, avval yuborilganlari qayta yuborilmaydi.

## Loyiha tuzilishi

```
app/
├── admin/            # Starlette-Admin panel (auth provider, view'lar)
├── middleware/        # Qo'shimcha middleware'lar
├── routers/           # API endpointlar (auth, user, waiter, kitchen, cashier)
├── schemas/           # Pydantic request/response modellari
├── config.py           # Muhit sozlamalari (pydantic-settings)
├── database.py         # SQLAlchemy engine, session, Base
├── dependencies.py    # JWT auth va rolga asoslangan dependency'lar
├── models.py            # SQLAlchemy ORM modellari
├── main.py               # FastAPI app, routerlar, statik fayllar
└── utils.py               # Parol hash, JWT generatsiya/dekod

frontend/
├── css/                 # Dizayn tizimi (index.css, panels.css)
├── js/
│   ├── api.js            # Backend bilan so'rov qatlami
│   ├── app.js            # SPA router va rolga qarab dashboard tanlash
│   ├── store.js          # localStorage asosidagi holat va toast xabarlar
│   └── pages/            # login, waiter, kitchen, cashier sahifalari
└── index.html

migrations/             # Alembic migratsiyalari
media_uploads/          # Yuklangan rasm fayllar (avatar, menyu rasmlari)
```

## Ishlab chiqish (dev) buyruqlari

```bash
# Linter
uv run ruff check .

# Avtomatik tuzatish
uv run ruff check --fix .

# Migratsiya yaratish (model o'zgargandan keyin)
uv run alembic revision --autogenerate -m "tavsif"

# Serverni qayta yuklash rejimida ishga tushirish
uv run uvicorn app.main:app --reload
```

## Xavfsizlik eslatmalari

- Production muhitida `CORSMiddleware`dagi `allow_origins=["*"]` qiymatini haqiqiy frontend domeningizga almashtiring.
- `SECRET_KEY` va `.env` fayli hech qachon versiya nazoratiga qo'shilmasligi kerak.
- Admin panel cookie orqali ishlaydi va `secure=True` bilan sozlangan — shuning uchun production'da albatta **HTTPS** ishlatilishi shart, aks holda cookie brauzerga saqlanmaydi.
- Har bir yangi xodim faqat admin tomonidan, admin JWT tokeni bilan yaratiladi (`/auth/user-create`).

---

## Litsenziya

Ushbu loyiha [MIT License](LICENSE) asosida tarqatiladi.
