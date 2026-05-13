# Local setup guide (Windows & macOS)

This document is a hands-on setup walkthrough for newcomers. It complements the repository [README.md](README.md); for feature overview, layout tables, demo accounts, and sample flows, use the README.

## Overview

The KT Automation monorepo contains a **Next.js 14** frontend in `apps/web` and a **FastAPI** backend in `apps/api`. The API serves sessions, AI processing, documents, RAG chat, and dashboard metrics. The web app talks to the API over HTTP. SQLite and Chroma storage paths are configured in environment variables (see [Environment files](#environment-files)).

## Prerequisites

Install the following before you begin.

- **Node.js 18+** (the project uses Next.js 14; see `apps/web/package.json`).
- **Python 3.11+** (3.12 is recommended; `apps/api/pyproject.toml` requires `>=3.11`).
- **Git** for cloning.
- **Optional:** Docker and Docker Compose if you want to run stack in containers instead of locally (see [Optional Docker](#optional-docker)).

On **Windows**, use a recent **PowerShell** or **Command Prompt**, or run the same commands from **Git Bash** where paths behave like Unix (forward slashes).

On **macOS** (and Linux), the examples below assume **zsh** or **bash** in Terminal.

## Clone & layout

Clone the repository, then open the root folder (the one that contains `apps/`, `data/`, and `docs/`).

- **`apps/web`** — Next.js UI (`npm run dev` serves on port 3000 by default).
- **`apps/api`** — FastAPI app (`uvicorn` serves on port 8000 in the Quick start).
- **`data/samples`**, **`data/role_config.json`** — sample data and UI role mapping (see README for behavior).

Commands in this guide assume your shell’s current directory is the **repository root** unless a step explicitly says `cd` into `apps/web` or `apps/api`.

## Environment files

**API and shared settings (repository root).**

1. From the repository root, copy the example env file to a real `.env` file. The API loads the **`.env` file at the repository root** first, then an optional **`apps/api/.env`** if present (later values override). The README Quick start uses the root `.env` only.

   - **macOS / Linux / Git Bash:**

     ```bash
     cp .env.example .env
     ```

   - **Windows PowerShell** (from repo root):

     ```powershell
     Copy-Item .env.example .env
     ```

   - **Windows cmd:**

     ```cmd
     copy .env.example .env
     ```

2. Edit `.env` as needed. [`.env.example`](.env.example) documents:
   - `DATABASE_URL` (default SQLite file `kt_platform.db`),
   - `CHROMA_PERSIST_DIR` (default `./chroma_data`),
   - `DATA_UPLOAD_DIR` (default `./uploads`),
   - `CORS_ORIGINS` (browser origins allowed to call the API, e.g. `http://localhost:3000`),
   - `JWT_SECRET` (use a long random value in real deployments; README asks for at least 32 bytes),
   - `OPENAI_*` variables (optional; see [Common issues / troubleshooting](#common-issues--troubleshooting)).

Paths like `./chroma_data` and `./uploads` are **relative to the API process working directory** when you run locally, which should be **`apps/api`** (see API setup below).

**Web app (`apps/web`).**

From `apps/web`, copy the web example file so `NEXT_PUBLIC_API_URL` points at your API (default is `http://localhost:8000`).

- **macOS / Linux / Git Bash:**

  ```bash
  cd apps/web
  cp .env.example .env.local
  ```

- **Windows PowerShell:**

  ```powershell
  cd apps\web
  Copy-Item .env.example .env.local
  ```

You can skip `.env.local` if the default API URL in `apps/web/.env.example` matches your setup.

## API setup (venv, pip install, uvicorn)

Run these steps from **`apps/api`** so relative paths in `.env` resolve correctly.

1. **Create a virtual environment**

   - **macOS / Linux** (Python 3 is often `python3`):

     ```bash
     cd apps/api
     python3 -m venv .venv
     ```

   - **Windows** (use **py launcher** or **python** if `python3` is not on PATH):

     ```powershell
     cd apps\api
     python -m venv .venv
     ```

2. **Activate the virtual environment**

   - **macOS / Linux (zsh or bash):**

     ```bash
     source .venv/bin/activate
     ```

   - **Windows PowerShell:**

     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

     If execution policy blocks scripts, you may need to run PowerShell as Administrator once to allow the current user scope, or use cmd activation below.

   - **Windows cmd:**

     ```cmd
     .venv\Scripts\activate.bat
     ```

3. **Install the package in editable mode** (installs dependencies from `pyproject.toml`):

   ```bash
   pip install -e .
   ```

4. **Start the API** (from `apps/api` with the venv activated):

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Leave this terminal running while you develop.

- **OpenAPI:** http://localhost:8000/docs  
- **Health:** http://localhost:8000/api/v1/health  

On first startup, the database is created and sample data may be loaded if no users exist (see README).

## Web setup (npm install, dev server)

Use a **second terminal**; the API should still be running in the first.

1. Go to the web app directory:

   - **macOS / Linux:**

     ```bash
     cd apps/web
     ```

   - **Windows:**

     ```powershell
     cd apps\web
     ```

2. Install dependencies and start the dev server:

   ```bash
   npm install
   npm run dev
   ```

3. Open **http://localhost:3000** in your browser.

If you changed `NEXT_PUBLIC_API_URL`, restart `npm run dev` after editing `.env.local`.

## Optional Docker

From the **repository root**, you can build and run both services with Docker Compose:

```bash
docker compose up --build
```

- Put `OPENAI_API_KEY` in your environment when you start Compose if you need live LLM calls inside containers (same note as README).
- **Web:** http://localhost:3000  
- **API docs:** http://localhost:8000/docs  

SQLite and Chroma data persist in the **`kt_api_data`** Docker volume (see `docker-compose.yml`), not necessarily in the same paths as a local `.env` file.

## Verify it works

With the API and web dev servers running locally:

1. Visit **http://localhost:8000/api/v1/health** — you should get a successful health response.
2. Visit **http://localhost:8000/docs** — OpenAPI UI should load.
3. Visit **http://localhost:3000** — the Next.js app should load and be able to reach the API if `NEXT_PUBLIC_API_URL` and network settings match.

Use the demo logins and routes described in the README to exercise the full UI.

## Common issues / troubleshooting

**Ports 3000 and 8000**

- Next.js defaults to **3000**; the documented `uvicorn` command uses **8000**. If either port is in use, stop the other process or change the port:
  - For the API: use another `--port` value and update `NEXT_PUBLIC_API_URL` / browser bookmarks accordingly.
  - For Next.js: `npm run dev -- -p <port>` (and add that origin to `CORS_ORIGINS` in `.env` if it is not already there).

**CORS errors in the browser**

- The API reads **`CORS_ORIGINS`** from `.env` (see `.env.example`). Include the exact origin your browser uses (for example `http://localhost:3000` and `http://127.0.0.1:3000` are both listed in the example). Restart the API after changing `.env`.

**`OPENAI_API_KEY` is optional**

- If **`OPENAI_API_KEY`** is empty, the API uses deterministic stubs suitable for offline demos (README). Set a real key in **`.env`** (never commit secrets) when you want live summarization, FAQ generation, and chat. Optional variables such as **`OPENAI_BASE_URL`**, **`OPENAI_MODEL`**, **`OPENAI_EMBEDDING_MODEL`**, and **`OPENAI_USE_PSEUDO_EMBEDDINGS`** are documented in `.env.example`.

**SQLite and Chroma paths**

- **`DATABASE_URL`** default is `sqlite:///./kt_platform.db`, which creates **`kt_platform.db`** in the API’s current working directory—typically **`apps/api`** when you follow this guide.
- **`CHROMA_PERSIST_DIR`** defaults to `./chroma_data` under that same working directory.
- **`DATA_UPLOAD_DIR`** defaults to `./uploads` there as well. If files or indexes seem “missing,” confirm you started `uvicorn` from **`apps/api`** and that `.env` paths match where you run the process.

**Windows path separators**

- In PowerShell and cmd, use **backslashes** (`apps\api`) when changing directories on the command line. In `.env` and most tools, forward slashes are often accepted; stay consistent with what your shell and Python build expect.

**`python` vs `python3`**

- On macOS and many Linux installs, use **`python3`** to create the venv if **`python`** points to 2.x or is missing. On Windows, **`python -m venv .venv`** is the usual approach after installing Python from python.org or the Store.
