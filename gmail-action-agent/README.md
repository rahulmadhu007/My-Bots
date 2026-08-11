# Gmail Action Agent (Relay)

Multi-agent system that connects to Gmail (or a demo inbox), understands which emails need action, and surfaces them as notifications in a React UI.

Demo mode works **immediately** with no credentials.

## Architecture

```
                         ┌─────────────────────┐
                         │    Orchestrator     │
                         │ routes + quality    │
                         └─────────┬───────────┘
                                   │
     ┌───────────┬─────────┬───────┼────────┬────────────┐
     ▼           ▼         ▼       ▼        ▼            ▼
GmailFetcher ContextAgent Action Quality Notification  (reclassify
   Agent                 Classifier Agent    Agent      on quality fail)
     │                        │
     ▼                        ▼
Gmail API / mock        Heuristics (+ optional LLM)
     │
     ▼
 React frontend — Relay notifications
```

1. **Orchestrator** receives a task (`scan_inbox`, `refresh`, `reclassify`), picks specialists, logs every routing decision, and enforces a quality gate.
2. **GmailFetcherAgent** pulls recent mail (live Gmail or demo fixtures).
3. **ContextAgent** extracts intent, entities, deadlines, asks, and tone.
4. **ActionClassifierAgent** decides `needs_action`, urgency, action type, and a suggested next step.
5. **QualityAgent** catches false positives/negatives; orchestrator may re-route to reclassify.
6. **NotificationAgent** formats actionable items for the Relay UI.

## Quick start (demo)

```bash
cd gmail-action-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Terminal 1 — API
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — UI
cd ../frontend
npm install
npm run dev
```

Open http://localhost:5173 → **Scan inbox**.

## Gmail OAuth (optional)

1. Create an OAuth client in [Google Cloud Console](https://console.cloud.google.com/) (enable Gmail API).
2. Redirect URI: `http://localhost:8000/auth/callback`
3. Copy `.env.example` → `.env` and set `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`, or place `credentials.json` in the project root.
4. Click **Connect Gmail** in the UI (or open `GET /auth/url`).
5. Token is stored at `data/token.json`. Without credentials the API stays in **demo** mode.

Optional: set `GROQ_API_KEY` or `OPENAI_API_KEY` to refine classifications. Heuristics always work without keys.

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/status` | Mode, auth, last scan |
| GET | `/auth/url` | OAuth start URL |
| GET | `/auth/callback` | OAuth callback |
| POST | `/scan` | Run orchestrator pipeline |
| GET | `/notifications` | Cached notifications |
| POST | `/notifications/{id}/dismiss` | Dismiss |
| POST | `/notifications/{id}/complete` | Complete |
| GET | `/agents` | Registered agents |
| GET | `/pipeline/log` | Last routing / step log |

## Layout

```
gmail-action-agent/
  backend/          FastAPI + orchestrator + sub-agents
  frontend/         React (Vite) Relay UI
  data/             OAuth token (gitignored)
  requirements.txt
  .env.example
```
