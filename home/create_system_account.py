
from django.core.management import call_command
from home.models import *
admin_user = CustomUser.objects.get(username='Admin')

system_account, created = SystemAccount.objects.get_or_create(admin=admin_user)
if created:
    system_account.current_balance = 0  
    system_account.save()

