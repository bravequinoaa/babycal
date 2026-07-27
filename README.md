# BabyCal

Cat (Cookie & Snoopy) feeding-visit scheduler for the family. See [.claude/SPEC.md](.claude/SPEC.md) for the full product spec, [.claude/SYSTEM_DESIGN.md](.claude/SYSTEM_DESIGN.md) and [.claude/UML.md](.claude/UML.md) for architecture/data model.

## Local development

```bash
python -m venv .venv
./.venv/Scripts/activate        # Windows; use `source .venv/bin/activate` on Linux/Mac
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

By default (no `.env` file), settings fall back to a local `db.sqlite3` and `OTP_PROVIDER_ENABLED=False`, so logging in with any phone number that belongs to an active user works immediately with no SMS setup — this is the failover behavior described in SPEC.md section 3.

Run tests:

```bash
python manage.py test
```

## Docker deployment (OCI Compute VM, Ubuntu)

1. **Provision the VM** — Ubuntu on an OCI Compute instance, with Docker and the Docker Compose plugin installed, ports 80/443 open in the security list.
2. **Point your domain** at the VM's public IP (an A record).
3. **Copy the repo** to the VM and create your real env file:
   ```bash
   cp .env.example .env
   # edit .env: SECRET_KEY, ALLOWED_HOSTS, POSTGRES_PASSWORD, DOMAIN_NAME, EMAIL_* etc.
   ```
4. **First boot (HTTP only, no certs yet)** — the repo defaults `docker-compose.yml` to `nginx/conf.d/babycal-bootstrap.conf.template`, which serves plain HTTP so certbot's ACME challenge is reachable:
   ```bash
   docker compose up -d --build
   docker compose exec web python manage.py createsuperuser
   ```
   Visit `http://<your-domain>` to confirm the app loads.
5. **Obtain the first TLS certificate** with certbot's webroot method:
   ```bash
   docker compose run --rm certbot certonly --webroot -w /var/www/certbot \
     -d <your-domain> --email you@example.com --agree-tos --no-eff-email
   ```
6. **Switch to the full TLS config**: edit `docker-compose.yml`, change the `nginx` service's template mount from `babycal-bootstrap.conf.template` to `babycal.conf.template`, then:
   ```bash
   docker compose up -d --build nginx
   ```
   The `certbot` service already runs in the background renewing the cert every 12 hours.
7. From here on, `docker compose up -d --build` picks up new code; `docker compose exec web python manage.py migrate` for schema changes (also runs automatically on container start via `docker-entrypoint.sh`).

## Turning on real SMS (Twilio) later

Set `OTP_PROVIDER_ENABLED=True` and fill in `TWILIO_*` in `.env`, then replace the body of `sms/services.py::send_sms()` with a real Twilio client call — it's the only place that needs to change; every call site (login OTP, invites) already calls this one function.

## Notification email

Claims optionally email the parents (`Schedule.notify_parents_email`). Set real `EMAIL_*` / `EMAIL_BACKEND` (e.g. `django.core.mail.backends.smtp.EmailBackend`) in `.env` to actually send instead of just logging to console.
