from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drop the django_migrations table from the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS django_migrations;")
        self.stdout.write(self.style.SUCCESS('✅ تم حذف جدول django_migrations من قاعدة بيانات Railway بنجاح'))
