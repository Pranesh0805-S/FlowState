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

Email OTP is used for account registration and password recovery. Locally, you can configure the `PRODUCTIVITY_SMTP_*` values in the root `.env.local`. For a free Render deployment, use Resend's HTTPS API: set `RESEND_API_KEY` and `RESEND_FROM_EMAIL`. Configure a verified sender domain in Resend before sending OTPs to users. Render Free blocks outbound SMTP ports, so Gmail SMTP is not suitable there. The app creates a persistent local signing key in `database/.session_signing_key` if `PRODUCTIVITY_JWT_SECRET` is not configured.

## Data and migration

SQLite initializes automatically at `database/productivity.db` for local development. If `DATABASE_URL` is configured, the API uses PostgreSQL and creates its schema automatically. Existing SQLite/MySQL data is not imported automatically; export and migrate records first if you need to keep them.

## API documentation

With the API running, open [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs).

## Deploy (Vercel frontend + Render API)

The root `render.yaml` defines a **Free** Render FastAPI service with no paid disk. Create a free PostgreSQL database with Neon, copy its pooled connection string into Render's `DATABASE_URL`, and set `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, and `WEB_ORIGIN` when Render prompts for them. Neon Free currently provides up to 1 GB per project and 100 compute hours per month; check its current quota before launch. Render Free services sleep after 15 minutes without traffic, so the first request after idle can take about a minute. Render Free's own PostgreSQL expires after 30 days, so this setup uses Neon for persistent storage instead.

In Vercel, import the same repository and set the project Root Directory to `web`. Add `API_SERVER_URL` in the Vercel project environment variables, with the Render service URL followed by `/api` (for example, `https://flowstate-api.onrender.com/api`). Keep the local `.env.local` files out of Git.

## Android app

`mobile/android` is a native Android client. Its screens are rendered with Android views and it connects to the same authenticated API used by the web client at `https://flowstate-pranesh0805.vercel.app/api/`. The Android client includes sign-in, registration and email verification, password reset, dashboard, task editing and status changes, workflow board, calendar, activity, team spaces, profile updates, password changes, and sign-out. The Android session cookie is stored in the app's private preferences and is not included in Android backups.

Open `mobile/android` in Android Studio, select an emulator or connected phone, and click **Run**. The Vercel frontend and API configuration must be deployed and reachable for sign-in and synced data to work. To point the client at a different deployment, update `BASE_URL` in `mobile/android/app/src/main/java/com/pranesh/flowstate/ApiClient.java`.

The dashboard offers the current sideload APK at `/downloads/flowstate-android.apk`; committing to `main` makes it available after the connected Vercel project deploys. The APK is debug-signed for direct installation and requires Android 6.0 (API 23) or later. For Play Store publication or stable in-place upgrades across future releases, create and securely retain a private release signing key, then publish a release-signed APK or Android App Bundle.

The `web` directory remains the browser-based companion app; it shares accounts and data with the native Android app.
