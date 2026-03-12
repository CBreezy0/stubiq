# Contributing

Thanks for contributing to MLB Show Dashboard.

## Repository Structure
- `backend/` — FastAPI API, auth, analytics, persistence, Alembic migrations, backend tests
- `frontend/` — Next.js web dashboard
- `ios/` — SwiftUI iOS app and Xcode project generator
- `docs/` — architecture docs and diagrams
- `scripts/` — bootstrap, validation, and safety helpers

## Development Workflow
1. Create a feature branch from your main integration branch.
2. Set up backend and frontend dependencies using the example environment files.
3. Make focused changes with clear commits.
4. Run validation before opening a pull request.
5. Update documentation when behavior, setup, or architecture changes.

## Environment and Secrets
- Never commit real credentials, API keys, signing assets, or provider plist files.
- Use `.env.example`, `backend/.env.example`, and `frontend/.env.example` as the source of truth for local configuration.
- Run `./scripts/check-secrets.sh` before opening a PR.

## Running Tests and Builds
### Backend
```bash
cd backend
venv/bin/pytest app/tests -q
```

### Frontend
```bash
cd frontend
npm run build
```

### iOS
```bash
ruby ios/MLBShowDashboard/scripts/generate_project.rb
xcodebuild -quiet -project ios/MLBShowDashboard/MLBShowDashboard.xcodeproj -scheme MLBShowDashboard -sdk iphonesimulator -destination 'platform=iOS Simulator,name=iPhone 17' CODE_SIGNING_ALLOWED=NO build
```

Or run the combined validation script:

```bash
./scripts/validate.sh
```

## Pull Requests
When opening a PR:
- describe the user-facing and technical change clearly
- include setup or migration notes if needed
- mention any new environment variables
- include screenshots for UI changes when available
- keep scope tight and avoid unrelated cleanup

## Code Style
- Match the existing style of each project area
- Prefer small, reviewable changes
- Add or update tests when behavior changes
- Keep documentation current for setup-heavy or architecture-heavy changes
