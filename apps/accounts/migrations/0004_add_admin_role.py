# Generated manually for adding admin role

from django.db import migrations


def add_admin_role(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.get_or_create(name='admin')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_populate_roles'),
    ]

    operations = [
        migrations.RunPython(add_admin_role),
    ]
