# Frontend Dashboard

Next.js App Router frontend for the MLB The Show Diamond Dynasty market intelligence backend.

## Prerequisites

- Node.js 18+
- Railway API available at `https://stubiq-production.up.railway.app`

## Setup

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000/dashboard`.

## Build

```bash
cd frontend
npm run build
npm run start
```

## Environment

- `NEXT_PUBLIC_API_BASE_URL` — FastAPI base URL. Defaults to `https://stubiq-production.up.railway.app` in `.env.example`.
- For local API development, override it in `frontend/.env.local`, for example:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Routes

- `/dashboard` — market phase, launch alerts, flips, floor buys, roster targets, collection priorities, grind recommendation, top sells
- `/portfolio` — portfolio metrics, holdings, recommendations, manual add/remove controls
- `/settings` — runtime threshold editor for strategy settings

## Backend assumptions

The UI integrates with these backend routes:

- `GET /auth/me`
- `POST /auth/signup`
- `POST /auth/login`
- `GET /market/phases`
- `GET /market/flips`
- `GET /market/floors`
- `GET /investments/roster-update`
- `GET /collections/priorities`
- `GET /portfolio`
- `GET /portfolio/recommendations`
- `GET /grind/recommendations`
- `GET /settings/engine-thresholds`
- `PATCH /settings/engine-thresholds`
- `POST /portfolio/manual-add`
- `POST /portfolio/manual-remove`

If any backend section returns no data or a temporary error, the dashboard shows an empty/error state instead of raw JSON.
