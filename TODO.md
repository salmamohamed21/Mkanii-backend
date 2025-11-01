# TODO: Configure Database Connection from Environment Variables

## Steps to Complete:
- [x] Modify settings/base.py to use dj_database_url for DATABASES configuration
- [x] Create .env file with public DATABASE_URL for local development
- [ ] Set DATABASE_URL in Railway environment variables for production (private URL)
- [x] Test local database connection (Django check passed)
- [ ] Verify production deployment uses private connection

## Notes:
- dj-database-url and python-dotenv are already installed
- load_dotenv is already imported in settings/base.py
- Public URL: postgresql://postgres:WMDzHkuQvvZsplfuZcLPPnDQOVqBUurp@centerbeam.proxy.rlwy.net:45970/railway
- Private URL for Railway: postgresql://postgres:<PASSWORD>@postgres.railway.internal:5432/railway (set in Railway dashboard)
