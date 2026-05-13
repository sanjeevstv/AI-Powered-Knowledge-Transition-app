# Publishing and security checklist

Use this before pushing to GitHub or sharing the repo.

## Secret and privacy scan (performed for public readiness)

- **Removed** a root `.env` that contained a real LLM key and an internal corporate gateway URL. If that key ever left your machine, **rotate it** with your provider.
- **Regenerated** `apps/web/package-lock.json` using the public npm registry and added `apps/web/.npmrc` (`registry=https://registry.npmjs.org/`) so private Artifactory URLs are not embedded in the lockfile.
- **`.gitignore`** now explicitly includes `apps/api/.env`, `apps/web/.env.local`, `*.mov`, and `apps/api/uploads/` (runtime uploads).
- **`.env.example`** uses empty placeholders for secrets (`OPENAI_API_KEY`, `JWT_SECRET`, etc.); do not paste real values into tracked files.

Re-scan quickly before each push:

```bash
rg -i 'sk-[a-zA-Z0-9]{10,}|api[_-]?key\s*=\s*[^=\s]|BEGIN (RSA |OPENSSH )PRIVATE KEY|password\s*=\s*[^\s]' --glob '!package-lock.json'
rg -i 'artifactory|private-registry|onedrive' .
```

## Security and configuration (concise review)

| Topic | Notes |
|-------|--------|
| **JWT** | HS256 with `JWT_SECRET`. Uses dev default when `JWT_SECRET` is unset or blank locally; set a long random secret for any shared or production deployment. |
| **CORS** | `CORS_ORIGINS` is a comma-separated allowlist. `allow_credentials=True` — keep origins explicit (no wildcard) for real deployments. Docker Compose defaults to `http://localhost:3000`; add `http://127.0.0.1:3000` if you use that origin. |
| **RBAC** | `data/role_config.json` controls full vs limited UI in addition to DB roles. Restart the API after edits. Session creation and some actions require full access via `require_full_ui_access`. |
| **Dependencies** | Lockfiles + `pyproject.toml` / `package.json` should be kept current; run `npm audit` / your preferred Python scanner periodically. |
| **Registration** | `/auth/register` exists for prototyping; consider restricting or removing it if you expose the API publicly. |

No additional code changes were required beyond tightening env handling (empty `JWT_SECRET` in `.env` coerces to the dev default in `apps/api/app/config.py`).

## Git and GitHub push

If `git rev-parse --show-toplevel` from the project folder points at your home directory, initialize a **dedicated** repository inside this project:

```bash
cd /path/to/ai_kt
git init
git checkout -b main
git remote add origin https://github.com/sanjeevstv/AI-Powered-Knowledge-Transition-app.git
git add -A
git status   # confirm no .env or .venv
git commit -m "Describe your change."
git push -u origin main
```

If `git push` fails with authentication errors, use a **personal access token** (HTTPS) or **SSH** with a key added to GitHub; the agent environment may not have your credentials.

## Large binaries

- **`.mov`** files are gitignored; use a compressed **GIF** under `docs/` for demos (current demo is ~2 MB).
- Do not commit local SQLite DBs, `chroma_data/`, or `node_modules/`.
