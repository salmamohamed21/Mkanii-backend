# Mkani Backend API

Django REST Framework Backend for Mkani Platform

## Environment Setup

### Local Development

1. **Clone the repository and install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local configuration
```

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Start the development server:**
```bash
python manage.py runserver
```

### Production Deployment (Coolify on Hostinger)

#### Prerequisites
- Docker and Docker Compose installed
- Coolify running on your server
- PostgreSQL database configured
- Redis instance available

#### Deployment Steps

1. **Push to GitHub:**
```bash
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

2. **Configure Coolify:**
   - Connect your GitHub repository
   - Set Docker as the deployment method
   - Use the provided `Dockerfile` and `.dockerignore`

3. **Set Environment Variables in Coolify:**
```
DJANGO_SETTINGS_MODULE=settings.prod
ALLOWED_HOSTS=api.makanii.cloud
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://localhost:6379/0
GOOGLE_CLIENT_ID=your-google-id
GOOGLE_CLIENT_SECRET=your-google-secret
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

4. **Deploy via Coolify:**
   - Trigger manual deployment or enable auto-deploy on push
   - Monitor logs for any migration or initialization errors

## Project Structure

```
├── apps/
│   ├── accounts/        # User authentication & authorization
│   ├── buildings/       # Building management
│   ├── packages/        # Package/subscription management
│   ├── payments/        # Payment processing
│   ├── notifications/   # Real-time notifications (WebSocket)
│   └── core/           # Core utilities and services
├── settings/
│   ├── base.py         # Base Django settings
│   ├── dev.py          # Development settings
│   └── prod.py         # Production settings
├── static/             # Static files
├── media/              # User uploads
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Local development docker-compose
├── requirements.txt    # Python dependencies
├── manage.py          # Django management utility
├── wsgi.py            # WSGI application entry point
└── asgi.py            # ASGI application for WebSockets
```

## Key Features

- **Django 5.2** with DRF
- **JWT Authentication** with SimplJWT
- **WebSocket Support** with Channels
- **Real-time Notifications**
- **Celery** task queue with Redis
- **PostgreSQL** database
- **CORS** support for frontend integration
- **OpenAPI/Swagger** documentation

## Important Notes for Production

1. **Security:**
   - `DEBUG = False` in production
   - `SECURE_SSL_REDIRECT = True`
   - `SESSION_COOKIE_SECURE = True`
   - HSTS headers enabled

2. **Static Files:**
   - Collected automatically during container startup
   - Served from `/staticfiles` directory

3. **Database:**
   - Migrations run automatically on startup
   - Use `DATABASE_URL` environment variable

4. **WebSockets:**
   - Requires Redis for Channels
   - WebSocket connections via `/ws/` endpoints

## Troubleshooting

### ModuleNotFoundError: No module named 'mkani'
- Ensure `INSTALLED_APPS` uses correct app paths (e.g., `'apps.accounts'`)
- Not using project root as a Python package

### Static files not loading
- Run: `python manage.py collectstatic --noinput`
- Configure web server to serve `/staticfiles/`

### Database connection errors
- Verify `DATABASE_URL` environment variable
- Check PostgreSQL credentials and connectivity

### WebSocket connection issues
- Verify Redis URL is correct
- Check `CHANNEL_LAYERS` configuration

## API Documentation

API documentation available at:
- Swagger UI: `https://api.makanii.cloud/api/docs/swagger/`
- ReDoc: `https://api.makanii.cloud/api/docs/redoc/`
- OpenAPI Schema: `https://api.makanii.cloud/api/schema/`
