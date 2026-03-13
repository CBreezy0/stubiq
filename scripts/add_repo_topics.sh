#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-CBreezy0/stubiq}"

if ! command -v gh >/dev/null 2>&1; then
  echo "Error: GitHub CLI (gh) is required but not installed." >&2
  echo "Install it from https://cli.github.com/ and try again." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Error: GitHub CLI is not authenticated." >&2
  echo "Run 'gh auth login' and try again." >&2
  exit 1
fi

gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/${REPO}/topics" \
  --input - <<'JSON'
{
  "names": [
    "fastapi",
    "postgresql",
    "nextjs",
    "swiftui",
    "ios-app",
    "mlb-the-show",
    "sports-analytics",
    "marketplace",
    "trading-dashboard",
    "full-stack"
  ]
}
JSON

echo "Updated GitHub topics for ${REPO}."
