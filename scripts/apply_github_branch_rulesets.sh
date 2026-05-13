#!/usr/bin/env bash
# Apply branch rulesets + CODEOWNERS on every repo you own, using a PAT file (never paste PAT in chat).
#
# Prerequisites:
#   - PAT with access to Administration + Contents on each repo (classic: "repo" scope).
#   - jq + curl
#
# Usage:
#   printf '%s\n' 'YOUR_PAT' > .github_pat && chmod 600 .github_pat
#   ./scripts/apply_github_branch_rulesets.sh
#   ./scripts/apply_github_branch_rulesets.sh /path/to/patfile
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RULESET_NAME="Protect main (require PR + code owner)"
CODEOWNERS_BODY='* @sanjeevstv'

PAT_FILE="${1:-$REPO_ROOT/.github_pat}"
if [[ ! -f "$PAT_FILE" ]]; then
  echo "Missing PAT file: $PAT_FILE" >&2
  echo "Put your GitHub PAT on one line in that file (see scripts/push_github_pat.sh)." >&2
  exit 1
fi

PAT="$(tr -d '[:space:]' < "$PAT_FILE")"
if [[ -z "$PAT" ]]; then
  echo "PAT file is empty." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required (brew install jq)." >&2
  exit 1
fi

GH_API="https://api.github.com"
HDR_AUTH=(-H "Authorization: Bearer ${PAT}")
HDR_ACC=(-H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28")

b64_content() {
  printf '%s' "$1" | base64 | tr -d '\n'
}

ensure_codeowners() {
  local owner="$1" repo="$2" branch="$3"
  local path="repos/${owner}/${repo}/contents/.github/CODEOWNERS"
  local url="${GH_API}/${path}?ref=${branch}"
  local resp code
  resp="$(curl -sS -w "\n%{http_code}" "${HDR_AUTH[@]}" "${HDR_ACC[@]}" "$url")" || return 1
  code="$(echo "$resp" | tail -n1)"
  body="$(echo "$resp" | sed '$d')"

  if [[ "$code" == "200" ]]; then
    local existing_sha existing_b64 existing_plain
    existing_sha="$(echo "$body" | jq -r '.sha')"
    existing_b64="$(echo "$body" | jq -r '.content' | tr -d '\n')"
    existing_plain="$(echo "$existing_b64" | base64 -d 2>/dev/null || true)"
    if echo "$existing_plain" | grep -qE '^\s*\*\s+@sanjeevstv\s*$' || echo "$existing_plain" | grep -qF '* @sanjeevstv'; then
      echo "  CODEOWNERS already references @sanjeevstv — skip"
      return 0
    fi
    local merged="${existing_plain}
${CODEOWNERS_BODY}
"
    local payload
    payload="$(jq -n \
      --arg msg "chore: ensure @sanjeevstv in CODEOWNERS for branch rules" \
      --arg content "$(b64_content "$merged")" \
      --arg sha "$existing_sha" \
      --arg br "$branch" \
      '{message:$msg, content:$content, sha:$sha, branch:$br}')"
    curl -sS -X PUT "${HDR_AUTH[@]}" "${HDR_ACC[@]}" \
      -H "Content-Type: application/json" \
      "${GH_API}/${path}" -d "$payload" | jq -e '.commit.sha' >/dev/null
    echo "  CODEOWNERS updated on ${branch}"
    return 0
  fi

  if [[ "$code" == "404" ]]; then
    local payload
    payload="$(jq -n \
      --arg msg "chore: add CODEOWNERS for required reviews" \
      --arg content "$(b64_content "${CODEOWNERS_BODY}"$'\n')" \
      --arg br "$branch" \
      '{message:$msg, content:$content, branch:$br}')"
    curl -sS -X PUT "${HDR_AUTH[@]}" "${HDR_ACC[@]}" \
      -H "Content-Type: application/json" \
      "${GH_API}/${path}" -d "$payload" | jq -e '.commit.sha' >/dev/null
    echo "  CODEOWNERS created on ${branch}"
    return 0
  fi

  echo "  ERROR: unexpected GET CODEOWNERS HTTP ${code}: ${body}" >&2
  return 1
}

ruleset_json() {
  local branch_ref="refs/heads/$1"
  jq -n \
    --arg name "$RULESET_NAME" \
    --arg ref "$branch_ref" \
    '{
      name: $name,
      target: "branch",
      enforcement: "active",
      conditions: {ref_name: {include: [$ref], exclude: []}},
      rules: [
        {
          type: "pull_request",
          parameters: {
            required_approving_review_count: 1,
            dismiss_stale_reviews_on_push: false,
            require_code_owner_review: true,
            require_last_push_approval: false,
            required_review_thread_resolution: false
          }
        },
        {type: "deletion"},
        {type: "non_fast_forward"}
      ]
    }'
}

upsert_ruleset() {
  local owner="$1" repo="$2" branch="$3"
  local list_url="${GH_API}/repos/${owner}/${repo}/rulesets"
  local list
  list="$(curl -sS "${HDR_AUTH[@]}" "${HDR_ACC[@]}" "$list_url")"
  if ! echo "$list" | jq -e 'type=="array"' >/dev/null 2>&1; then
    echo "  ERROR listing rulesets: ${list}" >&2
    return 1
  fi
  local rs_id
  rs_id="$(echo "$list" | jq -r --arg n "$RULESET_NAME" '.[] | select(.name==$n) | .id' | head -n1)"
  local json
  json="$(ruleset_json "$branch")"
  local resp code
  if [[ -n "$rs_id" && "$rs_id" != "null" ]]; then
    resp="$(curl -sS -w "\n%{http_code}" -X PATCH "${HDR_AUTH[@]}" "${HDR_ACC[@]}" \
      -H "Content-Type: application/json" \
      "${list_url}/${rs_id}" -d "$json")"
  else
    resp="$(curl -sS -w "\n%{http_code}" -X POST "${HDR_AUTH[@]}" "${HDR_ACC[@]}" \
      -H "Content-Type: application/json" \
      "$list_url" -d "$json")"
  fi
  code="$(echo "$resp" | tail -n1)"
  body="$(echo "$resp" | sed '$d')"
  if [[ "$code" != "200" && "$code" != "201" ]]; then
    echo "  ERROR ruleset HTTP ${code}: ${body}" >&2
    return 1
  fi
  echo "$body" | jq -e '.id' >/dev/null
  if [[ -n "$rs_id" && "$rs_id" != "null" ]]; then
    echo "  Ruleset updated (id ${rs_id})"
  else
    echo "  Ruleset created"
  fi
}

echo "Listing repos (affiliation=owner)..."
page=1
all='[]'
while true; do
  chunk="$(curl -sS "${HDR_AUTH[@]}" "${HDR_ACC[@]}" \
    "${GH_API}/user/repos?affiliation=owner&per_page=100&page=${page}")"
  n="$(echo "$chunk" | jq 'length')"
  if [[ "$n" -eq 0 ]]; then break; fi
  all="$(jq -n --argjson acc "$all" --argjson c "$chunk" '$acc + $c')"
  if [[ "$n" -lt 100 ]]; then break; fi
  page=$((page + 1))
done

nrepos="$(echo "$all" | jq 'length')"
echo "Found ${nrepos} repo(s)."

echo "$all" | jq -c '.[]' | while read -r row; do
  owner="$(echo "$row" | jq -r '.owner.login')"
  name="$(echo "$row" | jq -r '.name')"
  branch="$(echo "$row" | jq -r '.default_branch')"
  echo "==> ${owner}/${name} (default: ${branch})"
  if ! ensure_codeowners "$owner" "$name" "$branch"; then
    echo "  FAILED: CODEOWNERS — skipping ruleset for this repo." >&2
    continue
  fi
  if ! upsert_ruleset "$owner" "$name" "$branch"; then
    echo "  FAILED: ruleset (need Administration: write on the repo for PAT)." >&2
  fi
done

echo "Done."
