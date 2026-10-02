# Flowstate

Flowstate is a desktop task and workflow manager built with Python and PyQt5. It includes an authenticated task board, calendar, activity timeline, dashboard, team workspaces, email OTP registration, and password recovery.

## Stack

- Python 3.10+
- PyQt5 desktop client
- SQLite database (built in; no server installation)
- bcrypt password hashing and signed session tokens

## Run locally

1. Install Python 3.10 or newer.
2. Install packages: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and configure email settings if you want OTP emails.
4. Start the application: `python client/main.py`.

The database initializes automatically at `database/productivity.db`. To store it elsewhere, set `PRODUCTIVITY_DB_PATH` to an absolute file path. Existing MySQL databases are not imported automatically; export and migrate your records before switching if they contain data you need.

## Email OTP setup

Set `PRODUCTIVITY_SMTP_EMAIL` and `PRODUCTIVITY_SMTP_APP_PASSWORD` to an SMTP sender account and app password. Optional settings are `PRODUCTIVITY_SMTP_HOST` and `PRODUCTIVITY_SMTP_PORT`. Without SMTP configuration, registration and password recovery requiring OTP will report that email delivery is unavailable.

## Security and data

Passwords are stored as bcrypt hashes. Recovery requires an email OTP. The local SQLite file is private app data and should not be committed. Configure `PRODUCTIVITY_JWT_SECRET` to a long, random value for sessions. `.env` is local-only and ignored by Git.
