#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py shell -c "
import os
from core.models import User

username = (os.getenv('BOOTSTRAP_ADMIN_USERNAME') or '').strip()
password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD') or ''
email = (os.getenv('BOOTSTRAP_ADMIN_EMAIL') or username).strip()

if not username or not password:
    print('Bootstrap admin skipped (missing BOOTSTRAP_ADMIN_USERNAME/BOOTSTRAP_ADMIN_PASSWORD)')
else:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email or username,
            'role': 'ADMIN',
            'is_active': True,
            'is_staff': True,
            'is_superuser': True,
        },
    )
    if created:
        user.set_password(password)
        user.save(update_fields=['password'])
        print(f'Bootstrap admin created: {username}')
    else:
        updates = []
        if not user.is_staff:
            user.is_staff = True
            updates.append('is_staff')
        if not user.is_superuser:
            user.is_superuser = True
            updates.append('is_superuser')
        if not user.is_active:
            user.is_active = True
            updates.append('is_active')
        if user.role != 'ADMIN':
            user.role = 'ADMIN'
            updates.append('role')
        if updates:
            user.save(update_fields=updates)
        print(f'Bootstrap admin already exists: {username}')
"
