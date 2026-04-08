# School Prefectorial Voting System

Production-oriented Flask + MySQL voting system for school prefect elections with secure admin workflow, controlled voter flow, duplicate-vote prevention, auditing, and results export (CSV/PDF).

## Features

- Admin authentication with bcrypt password hashing (via `passlib`)
- Election lifecycle: create, edit, delete-safe checks, open, pause, close
- Position management per election with display ordering
- Candidate management with optional photo upload
- Voter management: manual CRUD + CSV import with success/failure summary
- Voter verification (student ID + optional PIN)
- Ballot casting with one vote per position and one ballot per voter per election
- MySQL transaction-backed vote submission with rollback on failure
- Duplicate prevention in service logic and DB constraints
- Results tally, winner and tie detection, turnout metrics
- Result exports to CSV and PDF
- Audit logging for sensitive actions and operations
- Custom 404/500 pages, flash messaging, and CSRF protection

## Tech Stack

- Frontend: HTML5, CSS3, Vanilla JavaScript
- Backend: Python 3.11+
- Framework: Flask
- Database: MySQL
- Driver: `mysql-connector-python`
- Password hashing: `passlib` with bcrypt
- PDF export: `fpdf2`
- Testing: `pytest`
- Deployment: Gunicorn + Nginx

## Project Structure

```text
.
├── app.py
├── wsgi.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── sql/
│   ├── schema.sql
│   └── seed.sql
├── samples/
│   ├── voters_sample.csv
│   └── candidates_sample.csv
├── app/
│   ├── __init__.py
│   ├── routes/
│   ├── services/
│   ├── repositories/
│   ├── utils/
│   ├── templates/
│   └── static/
└── tests/
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```bash
   cp .env.example .env
   ```
4. Update DB credentials and secrets in `.env`.

## MySQL Setup

1. Ensure MySQL server is running.
2. Run schema:
   ```bash
   mysql -u root -p < sql/schema.sql
   ```
3. Optional seed:
   ```bash
   mysql -u root -p < sql/seed.sql
   ```

## Create First Admin

Use the CLI command:

```bash
flask --app app.py create-admin
```

## Run in Development

```bash
flask --app app.py run --host 0.0.0.0 --port 5000
```

Application entry points:

- Voter-facing mode: `http://localhost:5000/vote/`
- Admin login: `http://localhost:5000/admin/login`

## Voting Integrity and Privacy Notes

- Integrity:
  - Service-level duplicate checks before insert.
  - DB-level uniqueness constraints:
    - `ballots (election_id, voter_id)`
    - `ballot_items (ballot_id, position_id)`
  - Ballot writes use a single transaction.
- Privacy tradeoff:
  - `ballots` references `voter_id` to enforce one-student-one-vote and auditability.
  - This design prioritizes integrity and controlled operations over strict ballot anonymity.
  - For stronger anonymity, a tokenized unlinking design is possible but adds operational complexity.

## CSV Import and Export

- Import CSV format:
  - `student_id,full_name,class_name,pin`
- Export CSV includes:
  - election name, position, candidate, class, vote count, winner/tie status

## PDF Export

Admin can export printable school-style PDF reports with:

- election title/status
- generation timestamp
- per-position candidate table
- winner/tie indicators
- registered voters, ballots cast, turnout

## Running Tests

```bash
pytest -q
```

Tests use mocked services and app test mode to validate route behavior and core business rules without requiring destructive DB setup.

## Production Deployment (Gunicorn + Nginx)

### Gunicorn

```bash
gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:app
```

### Nginx Reverse Proxy (example)

```nginx
server {
    listen 80;
    server_name your-domain-or-ip;

    client_max_body_size 4M;

    location /static/ {
        alias /path/to/project/app/static/;
        access_log off;
        expires 7d;
    }

    location /uploads/ {
        alias /path/to/project/app/static/uploads/;
        access_log off;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Production Checklist

- Set strong `SECRET_KEY`
- Set `FLASK_ENV=production`
- Set `SESSION_COOKIE_SECURE=true` behind HTTPS
- Use restricted DB user instead of MySQL root
- Enable MySQL backups and log rotation
- Protect server with firewall and TLS

## Backup and Restore

Backup:

```bash
mysqldump -u <user> -p school_votes > school_votes_backup.sql
```

Restore:

```bash
mysql -u <user> -p school_votes < school_votes_backup.sql
```

Also back up:

- `app/static/uploads/`
- `.env` (securely)

## Security Notes

- All SQL queries use parameterized statements
- Admin and voter PIN hashes are not stored in plain text
- CSRF enabled for forms
- Session cookie behavior is environment-configurable
- File uploads use extension checks + filename sanitization + max-size limit
- Audit logs capture critical admin actions and export activity

## Known Simplifications

- Single active election at a time is enforced in service rules.
- Voter interface is single-session browser flow (optimized for operator desk mode).
- Tests are primarily unit/route behavior tests with mocking; optional MySQL integration tests can be added per environment.

