#!/usr/bin/env bash
set -o errexit

echo "Waiting for database..."
python - <<'PY'
import os
import sys
import time
import psycopg2

host = os.getenv("DB_HOST", "db")
port = int(os.getenv("DB_PORT", "5432"))
name = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

for attempt in range(1, 31):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=name,
            user=user,
            password=password,
            connect_timeout=5,
        )
        conn.close()
        print("Database is ready")
        sys.exit(0)
    except Exception as exc:
        print(f"DB not ready (attempt {attempt}/30): {exc}")
        time.sleep(2)

print("Database did not become ready in time")
sys.exit(1)
PY

echo "Running migrations..."
python manage.py migrate

echo "Bootstrapping admin..."
python manage.py shell -c "
import os
from core.models import User

username = os.getenv('BOOTSTRAP_ADMIN_USERNAME')
password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD')
email = os.getenv('BOOTSTRAP_ADMIN_EMAIL') or username

if username and password:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'role': 'ADMIN',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        },
    )
    user.set_password(password)
    user.is_staff = True
    user.is_superuser = True
    user.is_active = True
    user.role = 'ADMIN'
    user.save()
    print(f'Admin ready: {username}')
else:
    print('Admin bootstrap skipped')
"

echo "Starting Gunicorn..."
exec gunicorn appraisal_backend.wsgi:application --bind 0.0.0.0:8000
