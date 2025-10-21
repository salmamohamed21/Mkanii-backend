# Generated manually for populating roles

from django.db import migrations


def populate_roles(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    roles = ['union_head', 'resident', 'technician']
    for role_name in roles:
        Role.objects.get_or_create(name=role_name)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(populate_roles),
    ]
