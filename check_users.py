import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis.settings')

import django
django.setup()

from home.models import CustomUser

print("=== All Users ===")
for u in CustomUser.objects.all()[:10]:
    print(f"  {u.userID}: username='{u.username}', first_name='{u.first_name}', last_name='{u.last_name}', email='{u.email}'")
