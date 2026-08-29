# GoDostavka — serverga o'rnatish qo'llanmasi

Ubuntu 24.04 server uchun. Backend + admin panel.

---

## 0. GitHub'ga yuklash (kompyuterda, bir marta)

```bash
cd backend
git init
git add .
git commit -m "GoDostavka backend"
git branch -M main
git remote add origin https://github.com/FOYDALANUVCHI/godostavka.git
git push -u origin main
```

> `.env` fayli `.gitignore` da — GitHub'ga chiqmaydi (maxfiy). To'g'ri.

---

## 1. Serverda loyihani klonlash

```bash
mkdir -p /var/www && cd /var/www
git clone https://github.com/FOYDALANUVCHI/godostavka.git
cd godostavka
```

## 2. Virtual muhit va paketlar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. .env faylini yaratish

```bash
cp .env.example .env
nano .env
```

`.env` ichida quyidagilarni to'ldiring (SECRET_KEY ni yangi va uzun qiling):

```
SECRET_KEY=<pastdagi buyruq bilan yarating>
DEBUG=False
ALLOWED_HOSTS=duoo.uz,www.duoo.uz,189.74.96.246
USE_POSTGRES=True
DB_NAME=godostavka
DB_USER=godostavka_user
DB_PASSWORD=Duoo2026market
DB_HOST=localhost
DB_PORT=5432
CORS_ALLOW_ALL=True
CSRF_TRUSTED_ORIGINS=https://duoo.uz,https://www.duoo.uz
```

SECRET_KEY yaratish (natijani .env ga qo'ying):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

`nano` da saqlash: `Ctrl+O`, Enter, `Ctrl+X`.

## 4. Baza va statik fayllar

```bash
python manage.py migrate
python seed_regions.py          # 15 viloyat + tumanlar
python manage.py createsuperuser   # admin yaratish (telefon + parol)
python manage.py collectstatic --noinput
```

## 5. Gunicorn (test)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

Brauzerda `http://189.74.96.246:8000/admin/` ochilsa — ishlayapti.
`Ctrl+C` bilan to'xtating (keyin systemd bilan doimiy qilamiz).

---

Keyingi bosqichlar (systemd + Nginx + HTTPS) — 6-9 qadamlarda.
