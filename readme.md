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

## Deploy (Vercel frontend + Render API)

The root `render.yaml` defines the FastAPI service, health check, generated JWT secret, SMTP settings, and a persistent disk for SQLite. Create a Render Blueprint from this repository and provide the two SMTP values when prompted. The API uses one paid Render instance because persistent disks are not available on free web services.

In Vercel, import the same repository and set the project Root Directory to `web`. Add `API_SERVER_URL` in the Vercel project environment variables, with the Render service URL followed by `/api` (for example, `https://flowstate-api.onrender.com/api`). Keep the local `.env.local` files out of Git.

## Install on Android

The responsive web app includes an installable web manifest and Flowstate icons. After the HTTPS Vercel deployment is live, open it in Chrome on Android and choose **Install app** or **Add to Home screen**. The installed app and desktop site use the same hosted frontend and Render account data; while a workspace page is open, task and activity views refresh every 12 seconds and refresh again when the app returns to the foreground.

To package the deployed PWA as an APK, first deploy it to its final domain. Then use Bubblewrap with the deployed manifest URL:

```powershell
npx @bubblewrap/cli init --manifest="https://YOUR_VERCEL_DOMAIN/manifest.webmanifest" --directory="mobile/android"
npx @bubblewrap/cli build --manifest="mobile/android"
```

Bubblewrap needs Android build tools and creates a signing key during setup. Keep that key and its passwords private. For a full-screen Trusted Web Activity, publish Bubblewrap's generated Digital Asset Links JSON at `/.well-known/assetlinks.json` on the same Vercel domain. This URL and signing certificate are created only after your first deployment and APK setup.
