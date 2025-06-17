from django.apps import AppConfig

class ShoppinglistAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shoppinglist_app'

    def ready(self):
        from django.contrib.auth.models import Group
        from django.db.utils import OperationalError
        try:
            Group.objects.get_or_create(name='Admin')
            Group.objects.get_or_create(name='User')
        except OperationalError:
            pass  # Avoids errors during initial migrate
