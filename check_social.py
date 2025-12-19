import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis.settings')

import django
django.setup()

from allauth.socialaccount.models import SocialAccount

print("=== Social Accounts ===")
for sa in SocialAccount.objects.all():
    print(f"  Provider: {sa.provider}, User: {sa.user.username}, UserID: {sa.user.userID}")
    print(f"    Extra data: {sa.extra_data}")
