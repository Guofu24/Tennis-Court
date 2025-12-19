#!/usr/bin/env python
"""Script to create a superuser and setup site"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis.settings')
django.setup()

from home.models import CustomUser
from django.contrib.sites.models import Site

# Create or update Site
site, created = Site.objects.update_or_create(
    id=1,
    defaults={'domain': '127.0.0.1:2212', 'name': 'Tennis Court'}
)
print(f"Site: {site.domain}, Created: {created}")

# Check if admin2 exists
if CustomUser.objects.filter(username='admin2').exists():
    print("User 'admin2' already exists!")
    user = CustomUser.objects.get(username='admin2')
    print(f"Username: {user.username}, UserID: {user.userID}, Is Superuser: {user.is_superuser}, Is Staff: {user.is_staff}")
else:
    # Create superuser
    user = CustomUser.objects.create_superuser(
        username='admin2',
        email='admin2@gmail.com',
        password='admin123'
    )
    print(f"Superuser created successfully!")
    print(f"Username: {user.username}")
    print(f"UserID: {user.userID}")
    print(f"Is Superuser: {user.is_superuser}")
    print(f"Is Staff: {user.is_staff}")
    print(f"Role: {user.role}")
