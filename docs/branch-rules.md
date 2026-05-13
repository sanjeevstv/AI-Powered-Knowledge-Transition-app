# Branch rules (simple setup)

This mirrors the **lightweight, documented** style used in sibling repos such as  
[AI-Hyper-Personalization-Engine-for-Retail-Banking](https://github.com/sanjeevstv/AI-Hyper-Personalization-Engine-for-Retail-Banking) (README points to setup/design docs; enforcement lives in **GitHub Settings**, not in magic repo files).

Here you get:

1. **`.github/workflows/ci.yml`** — runs on pushes and PRs to **`main`** (web `npm run build`, API `compileall` after `pip install -e .`).
2. **`.github/branch-ruleset.example.json`** — optional **import** into GitHub **Rulesets** (see below).
3. **`.github/CODEOWNERS`** — default owner `@sanjeevstv` for code-owner review when you enable it on the rule.

## Apply on GitHub (pick one path)

### A. Repository ruleset (recommended, simple UI)

1. Repo → **Settings** → **Rules** → **Rulesets** → **New ruleset** → **New branch ruleset**.
2. Name it (e.g. `Protect main`).
3. **Target branches**: add pattern `main`.
4. Enable rules, for example:
   - **Require a pull request before merging**
   - **Require approvals** → `1`
   - **Require review from Code Owners** (uses [`.github/CODEOWNERS`](../.github/CODEOWNERS))
   - **Block force pushes**
5. **Create** / **Save**.

**Optional import:** On the ruleset screen, use **Import** (if shown) and paste the contents of [`.github/branch-ruleset.example.json`](../.github/branch-ruleset.example.json). Adjust counts or toggles if GitHub rejects a field; UI names can differ slightly by plan.

### B. Require CI to pass (optional)

After the first workflow run appears under **Actions**, edit the ruleset (or classic branch protection) and require the check **`CI / web`** (and **`CI / api`** if you want both).

### C. Classic branch protection

**Settings** → **Branches** → **Add rule** for `main` — align with the same ideas: PR required, approvals, code owners, no force push.

---

Rules are **not enforced by this markdown file**; they are enforced only after you save them in **GitHub Settings** for this repository.
