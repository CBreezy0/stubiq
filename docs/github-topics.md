# GitHub Topics

GitHub topics help people discover StubIQ by technology, platform, and problem domain.

For this repository, topics improve:
- search visibility on GitHub
- discoverability for FastAPI, Next.js, and SwiftUI developers
- domain relevance for sports analytics and marketplace tooling
- clarity around the repository being a full-stack product

## Current Topics

StubIQ uses these repository topics:
- `fastapi`
- `postgresql`
- `nextjs`
- `swiftui`
- `ios-app`
- `mlb-the-show`
- `sports-analytics`
- `marketplace`
- `trading-dashboard`
- `full-stack`

## How to Run the Script

The repository includes an automation script at `scripts/add_repo_topics.sh:1`.

### Requirements
- GitHub CLI installed: `gh`
- GitHub CLI authenticated with access to the repository

### Run it

From the repo root:

```bash
./scripts/add_repo_topics.sh
```

By default, the script updates:
- `CBreezy0/stubiq`

You can also pass a repository slug explicitly:

```bash
./scripts/add_repo_topics.sh CBreezy0/stubiq
```

## How the Script Works

The script calls the GitHub Topics API using `gh api` and replaces the repository topic list with the curated StubIQ topics.

## Updating Topics Later

If you want to change the topic list later:
1. Open `scripts/add_repo_topics.sh:1`
2. Update the values inside the JSON `names` array
3. Re-run the script

Example:

```bash
./scripts/add_repo_topics.sh
```

## Notes

- The Topics API call replaces the topic set for the repository, so keep the full desired list in the script.
- If `gh` is not authenticated, run:

```bash
gh auth login
```
