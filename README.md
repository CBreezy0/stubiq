# MLB Show Dashboard

An open-source MLB The Show market intelligence platform with a FastAPI backend, a Next.js web dashboard, and a SwiftUI iOS client.

The project combines market ingestion, flips and floor-buy scanning, roster-update analysis, portfolio tracking, collection strategy, user-scoped settings, JWT auth, Google sign-in, Apple sign-in, and console connection scaffolding for Xbox and PlayStation.

## Screenshots
| Web Dashboard | iOS Dashboard | Portfolio |
| --- | --- | --- |
| _Add screenshot in `docs/images/web-dashboard.png`_ | _Add screenshot in `docs/images/ios-dashboard.png`_ | _Add screenshot in `docs/images/portfolio.png`_ |

## Repository Layout
- `backend/` — FastAPI, SQLAlchemy, Alembic, PostgreSQL integrations, tests
- `frontend/` — Next.js dashboard for desktop and browser workflows
- `ios/` — SwiftUI iOS application and Xcode project generator
- `docs/` — architecture notes, diagrams, and supporting documentation
- `scripts/` — setup, validation, and repository safety helpers

## Architecture Overview
High-level flow:
- `frontend/` and `ios/` both talk to the FastAPI API in `backend/`
- `backend/` manages auth, portfolio ownership, settings, analytics, and console connection state
- PostgreSQL stores users, refresh tokens, settings, connections, portfolio positions, and analytics tables
- External integrations include Google auth, Apple identity token verification, MLB The Show market data, MLB stats data, and future Xbox/PlayStation OAuth providers

A Mermaid architecture diagram lives in `docs/architecture.md:1`.

## Prerequisites
- Python `3.11+` recommended for the backend
- Node.js `18+` for the frontend
- Xcode `16+` and iOS Simulator for the iOS app
- PostgreSQL `14+` for local backend persistence
- Ruby with the `xcodeproj` gem for regenerating the iOS project

## Setup Instructions
### 1. Bootstrap dependencies
You can use the helper script:

```bash
./scripts/bootstrap.sh
```

Or install manually using the service-specific sections below.

### 2. Configure environment variables
Never commit real secrets. Copy values from example files only:

- Root reference: `.env.example`
- Backend source of truth: `backend/.env.example`
- Frontend source of truth: `frontend/.env.example`

Typical local copies:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

## Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Backend API defaults to `http://127.0.0.1:8000`.

### Backend Notes
- Tests: `venv/bin/pytest app/tests -q`
- Main app entrypoint: `backend/app/main.py`
- Seed helper: `backend/scripts/seed_dev.py`
- Auth and connection routes live under `backend/app/api/routes/`

## Frontend Setup
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Frontend defaults to `http://localhost:3000` and reads the API base URL from `NEXT_PUBLIC_API_BASE_URL`.

### Frontend Notes
- Production build: `npm run build`
- Start production server: `npm run start`
- Main dashboard route: `http://localhost:3000/dashboard`

## iOS Setup
Generate the Xcode project first:

```bash
ruby ios/MLBShowDashboard/scripts/generate_project.rb
```

Then:
- Open `ios/MLBShowDashboard/MLBShowDashboard.xcodeproj`
- Select an iPhone simulator
- Build and run from Xcode

### iOS Notes
- The app supports backend JWT auth plus Google and Apple sign-in flows
- Google sign-in requires the Firebase/GoogleSignIn packages and `GoogleService-Info.plist`
- Apple sign-in requires the Xcode capability and a matching backend `APPLE_CLIENT_ID`
- Console linking works in placeholder/mock mode until official provider credentials are available

See `ios/MLBShowDashboard/README.md:1` for mobile-specific setup details.

## Environment Variables
Use example files as the source of truth.

### Backend
Configured in `backend/.env.example` and typically copied to `backend/.env`.

Important values:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `APPLE_CLIENT_ID`
- `XBOX_CLIENT_ID`
- `XBOX_CLIENT_SECRET`
- `PLAYSTATION_CLIENT_ID`
- `PLAYSTATION_CLIENT_SECRET`
- `ENABLE_MOCK_CONSOLE_CONNECTIONS`
- `AUTH_RATE_LIMIT_MAX_REQUESTS`
- `AUTH_RATE_LIMIT_WINDOW_SECONDS`

### Frontend
Configured in `frontend/.env.example` and typically copied to `frontend/.env.local`.

Important values:
- `NEXT_PUBLIC_API_BASE_URL`

### iOS
The iOS app does not rely on a checked-in `.env` file. Backend targets are configured in-app, and provider setup is documented in `ios/MLBShowDashboard/README.md:1`.

## Launch Instructions
### Full web stack
If your backend virtualenv and frontend dependencies are already installed:

```bash
./start.sh
```

That starts:
- FastAPI at `http://127.0.0.1:8000`
- Next.js at `http://localhost:3000/dashboard`

### Service-by-service
Backend:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm run dev
```

iOS:
- Run the app from Xcode after generating the project

## Validation
Use the repo validation helper before pushing:

```bash
./scripts/check-secrets.sh
./scripts/validate.sh
```

## License
MIT — see `LICENSE:1`.

## Contributing
See `CONTRIBUTING.md:1` for workflow, testing, and pull request guidance.
