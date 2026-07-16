import os
from django.contrib.auth import get_user_model
from django.db import migrations


def create_admin(apps, schema_editor):
    User = get_user_model()
    username = os.environ.get("DJANGO_ADMIN_USERNAME", "admin")
    password = os.environ.get("DJANGO_ADMIN_PASSWORD")
    if not password:
        return  # Skip if no password configured
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=os.environ.get("DJANGO_ADMIN_EMAIL", "admin@example.com"),
            password=password,
        )


def remove_admin(apps, schema_editor):
    User = get_user_model()
    User.objects.filter(is_superuser=True, username__startswith="admin").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_socialplatform_platformstat"),
    ]

    operations = [
        migrations.RunPython(create_admin, remove_admin),
    ]