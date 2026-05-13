# Repository access: only the owner may change `main`

GitHub does **not** read a magic file that blocks pushes. You enforce this in **repository settings** (and optionally **organization** settings). Below is a practical setup for a personal repo owned by **`sanjeevstv`**.

## 1. Who can push at all?

1. Open the repo on GitHub → **Settings** → **Collaborators and teams** (or **Manage access**).
2. Ensure **no other user or team** has **Admin** or **Write** access.  
   - **Read** or **Triage** is fine for viewers.  
   - Only **you** (`sanjeevstv`) should have **Admin** (owner always can).

If someone needs to contribute, use **fork + pull request** and keep them without **Write** on the upstream repo.

## 2. Branch protection on `main` (recommended)

**Settings** → **Branches** → **Branch protection rules** → **Add rule** (or use **Rulesets**: **Settings** → **Rules** → **Rulesets** → **New ruleset**).

Target branch: **`main`**.

Enable as many of these as your GitHub plan allows:

| Setting | Purpose |
|--------|---------|
| **Require a pull request before merging** | Stops direct pushes to `main`; changes go through PRs. |
| **Require approvals** (e.g. 1) | PRs need an approval before merge. |
| **Require review from Code Owners** | Works with [`.github/CODEOWNERS`](../.github/CODEOWNERS) so **you** are the required reviewer for every path. |
| **Restrict who can push to matching branches** | If available, list **only your account** so only you can push to `main` (others use PRs from forks or branches if you allow). |
| **Do not allow bypassing the above settings** | Prevents admins from skipping checks unless you explicitly allow yourself only. |
| **Include administrators** (enforce on admins) | Optional: applies rules to you too; pair with **Allow specified actors to bypass** for only you if you still want direct pushes sometimes. |

Exact names vary slightly between **classic branch protection** and **repository rulesets**; both live under **Settings**.

## 3. `CODEOWNERS` (already in this repo)

The file [`.github/CODEOWNERS`](../.github/CODEOWNERS) assigns **`@sanjeevstv`** as code owner for `*`.  
Turn on **Require review from Code Owners** on `main` so merges require your review (combine with **no extra writers** so only you can merge if you are the only approver).

If your GitHub username is not `sanjeevstv`, edit `.github/CODEOWNERS` to the correct `@handle`.

## 4. Organizations

If the repo moves under an **organization**, an org owner can set **base permissions** to **Read** for all members, then grant **Write** only to you on this repository.

## 5. What this repo cannot do

- **`.github/CODEOWNERS`** does not block pushes by itself.  
- **Cursor / IDE rules** (e.g. under `.cursor/rules`) only guide **local AI**; they do **not** change GitHub permissions.

## 6. Quick verification

After configuration, log in as another GitHub user (or use a second account) with only **Read** access: they should **not** be able to push to `main` or merge without your policy allowing it.
