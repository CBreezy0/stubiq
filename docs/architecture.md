# Architecture Diagram

This diagram shows how the backend, frontend, iOS app, database, and external providers fit together.

```mermaid
flowchart LR
    Web[Next.js Frontend\nfrontend/] --> API[FastAPI Backend\nbackend/app/main.py]
    iOS[SwiftUI iOS App\nios/MLBShowDashboard] --> API

    API --> DB[(PostgreSQL)]
    API --> Show[MLB The Show Market APIs]
    API --> Stats[MLB Stats API]

    iOS --> Google[Google Sign-In]
    iOS --> Apple[Sign in with Apple]
    API --> GoogleVerify[Google Token Verification]
    API --> AppleVerify[Apple JWKS Verification]

    API --> Xbox[Xbox OAuth Scaffold]
    API --> PSN[PlayStation OAuth Scaffold]

    subgraph Backend Domains
        Auth[Auth + Sessions]
        Portfolio[Portfolio + Settings]
        Analytics[Market / Recommendations]
        Connections[Console Connections]
    end

    API --> Auth
    API --> Portfolio
    API --> Analytics
    API --> Connections
```

## Notes
- The web frontend and iOS app both use the same FastAPI backend.
- PostgreSQL stores user accounts, refresh tokens, user settings, portfolio data, connection state, and analytics records.
- Google and Apple auth are verified server-side.
- Xbox and PlayStation integrations are structured for future real OAuth support while keeping mock mode usable today.
