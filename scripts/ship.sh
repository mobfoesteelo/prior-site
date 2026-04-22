#!/usr/bin/env bash
# One-shot deploy script. Run after:
#   1. `gh auth login` is done
#   2. 5 keys are exported as env vars (see below)
#
# Usage:
#   export ANTHROPIC_API_KEY=sk-ant-...
#   export X_API_KEY=...
#   export X_API_SECRET=...
#   export X_ACCESS_TOKEN=...
#   export X_ACCESS_TOKEN_SECRET=...
#   bash scripts/ship.sh

set -euo pipefail

REPO_NAME="prior-site"

# ── 1. Verify prereqs ───────────────────────────────────────
echo "─── prereqs ───"
command -v gh >/dev/null || { echo "gh not installed"; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "run 'gh auth login' first"; exit 1; }
for v in ANTHROPIC_API_KEY X_API_KEY X_API_SECRET X_ACCESS_TOKEN X_ACCESS_TOKEN_SECRET; do
  [ -n "${!v:-}" ] || { echo "missing env var: $v"; exit 1; }
done
echo "  ✓ gh authenticated"
echo "  ✓ all 5 keys present"

# ── 2. Create GitHub repo + push (private) ──────────────────
echo "─── create repo + push ───"
if gh repo view "$REPO_NAME" >/dev/null 2>&1; then
  echo "  ✓ repo $REPO_NAME already exists, skipping create"
  git remote add origin "https://github.com/$(gh api user --jq .login)/$REPO_NAME.git" 2>/dev/null || true
  git push -u origin main
else
  gh repo create "$REPO_NAME" --private --source=. --push
  echo "  ✓ repo created + pushed"
fi

# ── 3. Load all 5 secrets into GitHub Actions ───────────────
echo "─── load secrets ───"
for v in ANTHROPIC_API_KEY X_API_KEY X_API_SECRET X_ACCESS_TOKEN X_ACCESS_TOKEN_SECRET; do
  echo -n "${!v}" | gh secret set "$v" --repo "$(gh api user --jq .login)/$REPO_NAME" --body -
  echo "  ✓ $v"
done

# ── 4. Kick off the first bot run manually ──────────────────
echo "─── trigger first run ───"
gh workflow run prior-bot.yml --repo "$(gh api user --jq .login)/$REPO_NAME"
echo "  ✓ workflow kicked"
echo ""
echo "tail with:   gh run watch --repo $(gh api user --jq .login)/$REPO_NAME"
echo ""
echo "site:        https://prior-site.vercel.app"
echo "x account:   https://x.com/prior_agent  (whichever handle you created)"
echo "repo:        https://github.com/$(gh api user --jq .login)/$REPO_NAME"
echo "feed json:   https://prior-site.vercel.app/api/log.json"
