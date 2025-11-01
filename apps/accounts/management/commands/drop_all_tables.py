from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drop all tables from the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Get all table names in the public schema
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
        self.stdout.write(self.style.SUCCESS('All tables dropped successfully'))
