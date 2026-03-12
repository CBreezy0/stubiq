#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

status=0

printf '[check-secrets] scanning for non-example env files\n'
while IFS= read -r file; do
  case "$file" in
    ./.env.example|./backend/.env.example|./frontend/.env.example)
      ;;
    *)
      echo "Potential secret-bearing env file found: ${file#./}"
      status=1
      ;;
  esac
done < <(find . -type f \( -name '.env' -o -name '.env.*' \) \
  ! -path './frontend/node_modules/*' \
  ! -path './frontend/.next/*' \
  ! -path './backend/venv/*')

printf '[check-secrets] scanning for private keys or signing assets\n'
while IFS= read -r file; do
  echo "Sensitive file pattern found: ${file#./}"
  status=1
done < <(find . -type f \( -name '*.pem' -o -name '*.key' -o -name '*.p12' -o -name '*.mobileprovision' -o -name 'GoogleService-Info.plist' \) \
  ! -path './frontend/node_modules/*' \
  ! -path './frontend/.next/*' \
  ! -path './backend/venv/*')

if rg -n --hidden --glob '!frontend/node_modules/**' --glob '!frontend/.next/**' --glob '!backend/venv/**' 'BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY' . >/dev/null 2>&1; then
  echo 'Private key material detected in repository files.'
  status=1
fi

if [ "$status" -ne 0 ]; then
  echo '[check-secrets] failed'
  exit 1
fi

echo '[check-secrets] ok'
