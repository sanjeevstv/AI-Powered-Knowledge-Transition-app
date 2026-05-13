#!/usr/bin/env bash
# Push current branch to sanjeevstv/AI-Powered-Knowledge-Transition-app using a PAT from a file.
# Usage:
#   echo 'YOUR_NEW_PAT' > .github_pat && chmod 600 .github_pat
#   ./scripts/push_github_pat.sh
#   ./scripts/push_github_pat.sh /path/to/patfile
#   ./scripts/push_github_pat.sh /path/to/patfile --force   # required after history rewrite (git push -f)
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

FORCE=()
PAT_FILE="$REPO_ROOT/.github_pat"
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f | --force) FORCE=(-f) ;;
    *) PAT_FILE="$1" ;;
  esac
  shift
done

if [[ ! -f "$PAT_FILE" ]]; then
  echo "Missing PAT file: $PAT_FILE" >&2
  echo "Create it with your GitHub PAT on a single line (repo root .github_pat is gitignored)." >&2
  exit 1
fi

PAT="$(tr -d '[:space:]' < "$PAT_FILE")"
if [[ -z "$PAT" ]]; then
  echo "PAT file is empty." >&2
  exit 1
fi

BR="$(git rev-parse --abbrev-ref HEAD)"
URL="https://oauth2:${PAT}@github.com/sanjeevstv/AI-Powered-Knowledge-Transition-app.git"

# Avoid writing token into .git/config; one-shot push (no -u to URL with credentials).
set +o history 2>/dev/null || true
export GIT_TERMINAL_PROMPT=0
git push "${FORCE[@]}" "$URL" "$BR"
