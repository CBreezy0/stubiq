#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf '\n[validate] secret hygiene\n'
"$ROOT_DIR/scripts/check-secrets.sh"

printf '\n[validate] backend tests\n'
cd "$ROOT_DIR/backend"
venv/bin/pytest app/tests -q

printf '\n[validate] frontend build\n'
cd "$ROOT_DIR/frontend"
npm run build

printf '\n[validate] iOS project generation\n'
cd "$ROOT_DIR"
ruby ios/MLBShowDashboard/scripts/generate_project.rb

printf '\n[validate] iOS simulator build\n'
xcodebuild -quiet \
  -project ios/MLBShowDashboard/MLBShowDashboard.xcodeproj \
  -scheme MLBShowDashboard \
  -sdk iphonesimulator \
  -destination 'platform=iOS Simulator,name=iPhone 17' \
  CODE_SIGNING_ALLOWED=NO build

printf '\n[validate] all checks passed\n'
