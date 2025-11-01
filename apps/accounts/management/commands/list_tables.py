from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'List all tables in the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
            tables = cursor.fetchall()
            if tables:
                self.stdout.write("Tables in public schema:")
                for table in tables:
                    self.stdout.write(f"- {table[0]}")
            else:
                self.stdout.write("No tables found in public schema.")
