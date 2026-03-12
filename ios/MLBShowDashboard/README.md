# MLB Show Dashboard iOS App

A production-leaning SwiftUI iOS client for the MLB The Show market intelligence backend in this repo.

## Highlights
- SwiftUI + MVVM
- Async/await networking with typed models
- Dark-mode-first premium dashboard design
- Backend JWT auth with Keychain session persistence
- Email/password, Google Sign-In, and Sign in with Apple flows
- Placeholder-friendly Xbox / PlayStation linking abstraction
- Reusable design system with glass cards, glow buttons, badges, charts, empty states, and loading skeletons
- Preview fixtures so screens render cleanly in Xcode immediately

## Project Layout
- `ios/MLBShowDashboard/MLBShowDashboard/App`
- `ios/MLBShowDashboard/MLBShowDashboard/Core`
- `ios/MLBShowDashboard/MLBShowDashboard/DesignSystem`
- `ios/MLBShowDashboard/MLBShowDashboard/Features`
- `ios/MLBShowDashboard/MLBShowDashboard/Networking`
- `ios/MLBShowDashboard/MLBShowDashboard/Auth`
- `ios/MLBShowDashboard/MLBShowDashboard/Connections`
- `ios/MLBShowDashboard/MLBShowDashboard/Models`
- `ios/MLBShowDashboard/MLBShowDashboard/ViewModels`
- `ios/MLBShowDashboard/MLBShowDashboard/Views`

## Setup
1. Open Terminal at the repo root.
2. Generate the Xcode project:
   - `ruby ios/MLBShowDashboard/scripts/generate_project.rb`
3. Open `ios/MLBShowDashboard/MLBShowDashboard.xcodeproj` in Xcode.
4. Choose an iPhone simulator and build.
5. Ensure the FastAPI backend is running locally if you want live auth/data instead of previews.

## Backend Configuration
The app supports three backend targets:
- `Local` → `http://127.0.0.1:8000`
- `Production` → placeholder production URL
- `Custom` → editable inside the Settings screen

If you run the FastAPI backend locally from this repo, the default local target works on the iOS Simulator.

## Google Sign-In Setup
To turn on real Google Sign-In token acquisition on iOS:
1. Add Swift Packages in Xcode:
   - `https://github.com/firebase/firebase-ios-sdk.git`
     - products: `FirebaseCore`, `FirebaseAuth`
   - `https://github.com/google/GoogleSignIn-iOS.git`
     - product: `GoogleSignIn`
2. Add `GoogleService-Info.plist` to the iOS target resources.
3. Add the reversed client ID from the plist as a URL type in the target settings.
4. Set the backend `GOOGLE_CLIENT_ID` to the same client used by the iOS app.

Without that configuration, the app still builds, but Google Sign-In shows a configuration message instead of completing.

## Sign in with Apple Setup
To turn on Sign in with Apple:
1. In Apple Developer, enable the Sign in with Apple capability for the app identifier.
2. In Xcode, add the `Sign in with Apple` capability to the iOS target.
3. Set the backend `APPLE_CLIENT_ID` to the Services ID / audience used by your app flow.
4. Build and test on a simulator or device signed into an Apple ID.

## Auth Flow
The app now exchanges auth with the backend directly:
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/google`
- `POST /auth/apple`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/revoke-sessions`
- `GET /auth/me`

Access and refresh tokens are stored in Keychain. On relaunch, the app refreshes the session automatically when a refresh token is present.

## Console Connections
`Account Connections` uses provider abstractions now:
- `XboxConnectionProvider`
- `PlayStationConnectionProvider`

Current behavior:
- If no official auth URL/callback is configured, the app uses mock placeholder linking.
- If official auth URLs are provided later, the provider classes already support `ASWebAuthenticationSession`.
- Console linking never blocks the rest of the app.

## Real-World Limitations
### Password reset
The forgot-password screen is still a placeholder because the backend does not yet expose a reset-email flow.

### Console account linking
The backend now exposes start, complete, and callback endpoints for Xbox/PlayStation, but real production console OAuth still depends on platform approval and provider-specific redirect/token-exchange details.

### Better charting endpoints
The app already renders charts, but these backend additions would improve fidelity:
- `GET /cards/{item_id}/history`
- `GET /portfolio/history`

## Notes
- The app compiles without blocking on console integrations.
- The dashboard remains useful before platform linking is live.
- Preview data lives in `ios/MLBShowDashboard/MLBShowDashboard/Models/PreviewFixtures.swift`.
