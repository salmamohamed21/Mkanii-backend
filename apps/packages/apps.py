from django.apps import AppConfig


class PackagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.packages'

    def ready(self):
        import apps.packages.signals  # noqa
