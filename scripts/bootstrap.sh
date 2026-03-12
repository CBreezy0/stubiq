#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf '\n[bootstrap] backend dependencies\n'
cd "$ROOT_DIR/backend"
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt

printf '\n[bootstrap] frontend dependencies\n'
cd "$ROOT_DIR/frontend"
npm install

printf '\n[bootstrap] iOS tooling check\n'
if ! ruby -e "require 'xcodeproj'" >/dev/null 2>&1; then
  echo "Install the xcodeproj gem before generating the Xcode project: gem install xcodeproj"
else
  echo "xcodeproj gem is available"
fi

printf '\n[bootstrap] done\n'
echo "Next steps:"
echo "  cp backend/.env.example backend/.env"
echo "  cp frontend/.env.example frontend/.env.local"
echo "  ruby ios/MLBShowDashboard/scripts/generate_project.rb"
