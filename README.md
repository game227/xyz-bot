# xyz-bot

Django 5.2 asosidagi ta'lim platformasi + Telegram bot (aiogram 3). Darslar, imtihonlar, obuna, jonli darslar va bildirishnomalar.

## Ilovalar (`apps/`)
`core` · `accounts` · `education` · `exam` · `progress` · `subscription` · `live` · `notifications` · `bot`

`_archive/` — olib tashlangan eski panel kodi (faqat ma'lumot uchun).

## Ishga tushirish
```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env     # SECRET_KEY, TELEGRAM_BOT_TOKEN va boshqalarni to'ldiring
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Sozlamalar (.env)
- SQLite default; PostgreSQL uchun `USE_POSTGRES=1` va `DB_*`
- Bot rejimi `BOT_MODE`: `polling` (dev) yoki `webhook` (production, HTTPS + `WEBHOOK_URL`)
- `ADMIN_TELEGRAM_IDS` — vergul bilan ajratilgan, botda avtomatik admin bo'ladi
- Tokenni hech qachon kodga yozmang

`.env`, `db.sqlite3`, `media/`, `logs/` commit qilinmaydi.
