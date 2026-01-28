# TerminFinder Deployment Guide

## Render Deployment

This application is configured for deployment on Render using the provided `render.yaml` and `gunicorn.conf.py` files.

### Files Overview

- **`render.yaml`**: Defines the Render services and database configuration
- **`gunicorn.conf.py`**: Gunicorn WSGI server configuration optimized for production

### Deployment Steps

1. **Connect Repository**: Connect your GitHub repository to Render
2. **Create Service**: Render will automatically detect the `render.yaml` file and create the services
3. **Configure Environment Variables**: Set the following environment variables in Render:
   - `STRIPE_SECRET_KEY`: Your Stripe secret key
   - `STRIPE_PUBLISHABLE_KEY`: Your Stripe publishable key
   - `MAIL_USERNAME`: SMTP username for email
   - `MAIL_PASSWORD`: SMTP password for email
   - `CELERY_BROKER_URL`: Redis URL (if using background tasks)
   - `CELERY_RESULT_BACKEND`: Redis URL (if using background tasks)

### Services Created

- **Web Service**: `terminfinder-api` - Main Flask application
- **Database**: `terminfinder-db` - PostgreSQL database with schema `terminfinder`

### Environment Variables

The following environment variables are automatically configured:
- `DATABASE_URL`: PostgreSQL connection string
- `DB_SCHEMA`: Set to `terminfinder`
- `FLASK_ENV`: Set to `production`
- `SECRET_KEY`: Auto-generated
- `JWT_SECRET_KEY`: Auto-generated

### Manual Configuration Required

Set these in Render dashboard (Environment tab):
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_DEFAULT_SENDER`

### Database Schema

The application uses PostgreSQL with a custom schema `terminfinder`. All tables are created automatically via Flask-Migrate.

### Health Check

The application includes a health check endpoint at `/health` that returns `{"status": "healthy"}`.

### Scaling

The current configuration is optimized for Render's free tier:
- 2 Gunicorn workers
- 1000 max requests per worker
- 30 second timeout

For higher traffic, consider upgrading the Render plan and adjusting worker count in `gunicorn.conf.py`.