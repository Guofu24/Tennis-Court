import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis.settings')

import django
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

print("=== Sites ===")
for s in Site.objects.all():
    print(f"  ID: {s.id}, Domain: {s.domain}, Name: {s.name}")

print("\n=== Social Apps ===")
for app in SocialApp.objects.all():
    print(f"  Provider: {app.provider}, Name: {app.name}")
    print(f"  Client ID: {app.client_id[:20]}..." if app.client_id else "  No Client ID")
    print(f"  Sites: {[s.domain for s in app.sites.all()]}")
