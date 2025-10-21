from django.apps import AppConfig


class PackagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mkani.apps.packages'

    def ready(self):
        import mkani.apps.packages.signals  # noqa
