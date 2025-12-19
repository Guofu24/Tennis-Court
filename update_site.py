import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tennis.settings')

import django
django.setup()

from django.contrib.sites.models import Site

# Update existing site to ngrok domain
site = Site.objects.get(id=1)
site.domain = 'sclerodermatous-bodhi-untimed.ngrok-free.dev'
site.name = 'Tennis Court (ngrok)'
site.save()

print(f"Updated Site: {site.domain}")

# Or if you want to use localhost, uncomment below:
# site.domain = '127.0.0.1:2212'
# site.name = 'Tennis Court'
# site.save()
