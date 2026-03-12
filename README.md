# StubIQ

> Real-time Diamond Dynasty market intelligence for MLB The Show.

StubIQ is a full-stack MLB The Show Diamond Dynasty market analytics platform built to monitor the in-game marketplace, surface profitable trading opportunities, and deliver modern decision support across web and iOS.

It combines real-time marketplace ingestion, liquidity analysis, flip detection, roster-upgrade investing signals, portfolio tracking, and user-friendly dashboards into a production-style tool for serious Diamond Dynasty traders.

## Overview

StubIQ tracks the MLB The Show marketplace, detects profitable flips, analyzes liquidity, predicts roster upgrade investments, and provides modern dashboards across web and iOS.

The platform is designed for players who want:
- faster visibility into market movement
- cleaner signals for buy/sell decisions
- better confidence around upgrade-driven investments
- one place to monitor flips, collections, and portfolio performance

## Screenshots

| Dashboard | Flips | Portfolio |
| --- | --- | --- |
| ![Dashboard Placeholder](docs/images/dashboard.png) | ![Flips Placeholder](docs/images/flips.png) | ![Portfolio Placeholder](docs/images/portfolio.png) |

## Features

- Real-time marketplace ingestion
- Flip opportunity detection
- Liquidity ranking engine
- Roster upgrade investment predictions
- Portfolio tracking
- Web analytics dashboard
- Native iOS app
- Authentication with Google / Apple
- Console account connection architecture

## Architecture

StubIQ follows a simple full-stack analytics pipeline:

```text
MLB Show API
      ↓
FastAPI ingestion engine
      ↓
PostgreSQL market database
      ↓
Analytics engine
      ↓
Web dashboard (Next.js)
iOS app (SwiftUI)
```

At a high level:
- the backend ingests and normalizes market data
- PostgreSQL stores user, market, portfolio, and recommendation state
- analytics services generate liquidity, flip, and roster-upgrade signals
- the web app and iOS app consume the same backend APIs

For a diagrammed version, see `docs/architecture.md:1`.

## Tech Stack

**Backend**
- FastAPI
- PostgreSQL
- SQLAlchemy
- APScheduler

**Frontend**
- Next.js
- TypeScript
- React
- Recharts

**Mobile**
- SwiftUI
- iOS networking with async/await

**Infrastructure**
- GitHub
- Docker support

## Repository Structure

```text
backend/
frontend/
ios/
docs/
scripts/
```

## Getting Started

```bash
git clone https://github.com/CBreezy0/stubiq.git
cd stubiq
```

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### iOS

```bash
ruby ios/MLBShowDashboard/scripts/generate_project.rb
```

Then open `ios/MLBShowDashboard/MLBShowDashboard.xcodeproj` in Xcode and run the app on a simulator.

## Configuration

Environment variables should come from example files, not committed secrets.

Use:
- `.env.example`
- `backend/.env.example`
- `frontend/.env.example`

Typical local setup:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Key backend variables include:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_REFRESH_SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `APPLE_CLIENT_ID`
- `ENABLE_MOCK_CONSOLE_CONNECTIONS`

Key frontend variable:
- `NEXT_PUBLIC_API_BASE_URL`

## Launch Instructions

### Run the web stack

```bash
./start.sh
```

This starts:
- FastAPI on `http://127.0.0.1:8000`
- Next.js on `http://localhost:3000/dashboard`

### Validate the repository

```bash
./scripts/check-secrets.sh
./scripts/validate.sh
```

## Development Notes

MLB The Show API behavior can vary around a new game launch. If current-season endpoints are not yet fully available, MLB25 endpoints may be used for testing until the new live marketplace is stable.

That makes StubIQ easier to iterate on before full release-day data is available.

## Roadmap

- Real console OAuth integration
- Public hosted dashboard
- iOS App Store release
- Advanced trading signals

## License

MIT License — see `LICENSE:1`.
