from django.apps import AppConfig
from django.contrib.auth import get_user_model
import sys


from django.db.utils import OperationalError, ProgrammingError

class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        if 'runserver' in sys.argv:
            try:
                User = get_user_model()
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_user(username='admin', password='admin123', user_type='admin')
            except (OperationalError, ProgrammingError):
                pass