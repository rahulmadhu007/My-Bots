# AGENTS.md

## Cursor Cloud specific instructions

This repo contains a single product, the **Performance Intelligence Agent**, living under `performance-agent/`. It is a Python FastAPI backend (a 6-agent employee-performance analysis pipeline) plus a static single-file frontend (`performance-agent/frontend/index.html`). There is no database; data comes from four bundled Excel files in `performance-agent/data/`.

### Services

- Backend (FastAPI/Uvicorn) — the core engine. Run from `performance-agent/backend/`:
  - `python3 -m uvicorn main:app --reload --port 8000`
  - Endpoints: `GET /health`, `GET /employees`, `POST /analyse` (body `{"employee_name": "..."}`).
  - Use `python3 -m uvicorn` (not the bare `uvicorn` command): pip installs the `uvicorn` script to `~/.local/bin`, which is not on `PATH`.
- Frontend — static file, no build step. Serve it with any static server and open in a browser, e.g. from `performance-agent/frontend/`:
  - `python3 -m http.server 3000` then open `http://localhost:3000/index.html`.

### Non-obvious caveats

- The frontend's `API_BASE` is hardcoded to `http://localhost:8000`, so the backend must be running on port 8000 for the UI to work.
- The frontend loads React, ReactDOM, PropTypes, Babel, Recharts, and Tailwind from CDNs (unpkg / cdn.tailwindcss.com), so it requires outbound internet at runtime; there is no local bundle. Recharts' UMD build needs the global `PropTypes`, which is why `prop-types` is loaded before `recharts` in `index.html`.
- Data loads eagerly on import of `data_loader` and again on FastAPI startup. `data_loader.py` resolves the data directory by falling back to `performance-agent/data/` (the first two hardcoded macOS paths don't exist here), so the bundled demo datasets work out of the box.
- `ANTHROPIC_API_KEY` is optional. The Synthesis Agent calls Anthropic Claude when the key is set; otherwise `synthesis_agent.py` uses a deterministic local fallback (`_fallback_synthesis`) that still computes scores/tiers. End-to-end analysis works without the key — only the AI-written correlation/narrative text is replaced by fallback text.
- Demo employees in the bundled data: Alex Morgan, Sarah Chen, James Patel, Priya Sharma (plus Emily Nguyen, Michael Torres).
- There are no automated tests, linter config, or git hooks in this repo.
