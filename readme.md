# Flowstate

Flowstate is a responsive productivity workspace for tasks, planning, and small teams. The frontend is built with Next.js 16 and React 19. A Python FastAPI service exposes the task, authentication, team, calendar, dashboard, and activity APIs. SQLite runs locally with no separate database server.

## Start the application

Use two terminals from the repository root.

### One-time setup

```powershell
python -m pip install -r requirements.txt
cd web
npm install
```

Copy `web/.env.example` to `web/.env.local` if you want to point the frontend to a non-default API URL. The default API URL is `http://127.0.0.1:8000/api`.

### Terminal 1 — API

From the repository root:

```powershell
python -m uvicorn server.api:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — web app

```powershell
cd web
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Email verification

Email OTP is used for account registration and password recovery. Configure `PRODUCTIVITY_SMTP_EMAIL` and `PRODUCTIVITY_SMTP_APP_PASSWORD` in the root `.env.local`. Optional values are `PRODUCTIVITY_SMTP_HOST` and `PRODUCTIVITY_SMTP_PORT`. The app creates a persistent local signing key in `database/.session_signing_key` if `PRODUCTIVITY_JWT_SECRET` is not configured.

## Data and migration

SQLite initializes automatically at `database/productivity.db`, or use `PRODUCTIVITY_DB_PATH` to select another path. Existing MySQL data is not imported automatically. Export and migrate records first if you need to keep them.

## API documentation

With the API running, open [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs).
