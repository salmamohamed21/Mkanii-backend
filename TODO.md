# Fix Django Module Import Errors

## Tasks
- [x] Update settings/base.py: Remove 'mkani.' prefix from INSTALLED_APPS, MIDDLEWARE, ROOT_URLCONF, WSGI_APPLICATION, ASGI_APPLICATION, AUTHENTICATION_BACKENDS
- [x] Update urls.py: Change includes to 'apps.*.urls'
- [x] Update asgi.py: Change import to 'apps.notifications.routing'
- [x] Update wsgi.py: Set DJANGO_SETTINGS_MODULE to 'settings.base'
- [x] Update manage.py: Set DJANGO_SETTINGS_MODULE to 'settings.base'
- [x] Update Procfile: Add --bind 0.0.0.0:$PORT
- [x] Test locally with `python manage.py runserver`
- [ ] Commit and redeploy to Railway
