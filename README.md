# Salon Management System

A Django-based salon management starter application with a responsive customer website, service catalogue, appointment booking, customer accounts and staff appointment management.

## Features

- Responsive landing page and searchable service catalogue
- Customer registration, login and logout
- Availability-aware appointment requests with configurable weekly hours, closed dates, service durations, and 15-minute slots
- Overlap prevention backed by unique database reservations; cancelled appointments release their slots
- Customer appointment history and cancellation
- Staff dashboard with appointment totals and status updates
- Staff-only service creation, editing and deletion
- Django admin for managing users, services and appointments
- SQLite database for local development; Nairobi timezone defaults

## Run locally

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Sign in to `/admin/` with the superuser account to add salon services and manage the application. The first superuser can use the staff dashboard at `/dashboard/`.

## Important production notes

Never reuse the development secret key for deployment. Provide a fresh `DJANGO_SECRET_KEY` in the host's secret environment settings.
Static catalogue images are part of the repository. Configure the optional S3-compatible media backend before staff upload service photos in production; otherwise uploads go to local disk and may disappear when an ephemeral web instance is replaced.

## Deploy to Render

1. Publish the project to a GitHub repository. Confirm `db.sqlite3`, `.env`, `.venv/`, `media/`, and `staticfiles/` are not committed.
2. In Render, create a managed PostgreSQL database and a **Web Service** connected to the repository. Choose Python 3.12 or newer (required by Django 6).
3. Set the Web Service build command to `bash build.sh` and the start command to `gunicorn salon_system.wsgi:application --bind 0.0.0.0:$PORT`.
4. Add environment variables to the Web Service:
	- `DJANGO_DEBUG` = `False`
	- `DJANGO_SECRET_KEY` = generate a new secret using Render's **Generate** option
	- `DATABASE_URL` = the database's **internal** connection URL; keep it secret
	- `CSRF_TRUSTED_ORIGINS` = `https://your-render-name.onrender.com` (and later `https://your-domain` when you connect a domain)
	- `ALLOWED_HOSTS` = `your-render-name.onrender.com` (and your custom domain when connected)
5. Before opening public signups, open the Render Shell and run `python manage.py migrate`, then `python manage.py createsuperuser`.
6. Configure an S3-compatible private bucket for uploaded images by setting `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_ACCESS_KEY_ID`, and `AWS_SECRET_ACCESS_KEY` on the Web Service. Add `AWS_S3_ENDPOINT_URL` if your provider requires a custom endpoint. The storage backend creates signed URLs; grant the credentials permission to upload, read, and delete objects. Back up the database and uploaded media. Review hosting, database, object-storage, and domain pricing before creating paid resources.
7. Deploy and test the Render-provided HTTPS URL. Add a custom domain in Render, set the DNS records shown there with your registrar, add the domain to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`, then wait for HTTPS to become active.
8. After the public site works, register the domain in Google Search Console and request indexing. Search engine discovery is not immediate.

The old development secret key was embedded in the source settings, so treat it as exposed and use a newly generated deployment secret. HSTS preload is enabled; keep it only if the domain and all its subdomains are permanently served over HTTPS. The deployed database starts empty unless you securely migrate existing records; never commit the local SQLite database or personal customer data. Do not post database URLs, passwords, or secret keys in source control or chat.
