# AI YouTube Semantic Search

A production-ready, AI-powered YouTube semantic search web app. Describe any video in natural language and a hierarchical multi-agent system finds and plays the best match — like ChatGPT meets YouTube.

## Features

- Natural-language video search powered by **Grok** (xAI)
- Hierarchical multi-agent pipeline (Manager + specialized sub-agents)
- Concurrent YouTube Data API v3 search with deduplication
- Semantic ranking, confidence scoring, and quality validation
- Autoplay React Player with controls
- Recent search history (localStorage)
- Dark / light theme, toasts, skeletons, Framer Motion transitions
- Keyboard shortcuts (`/` focus search, `T` toggle theme, `Enter` search)
- Clean Architecture: UI · Agents · Services · API · Utilities

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | React, Vite, TypeScript, TailwindCSS, React Query, Framer Motion, React Player, Axios |
| Backend | Node.js, Express, TypeScript |
| AI | Grok API (OpenAI-compatible SDK) |
| Video | YouTube Data API v3 |

## Architecture

```
User description
    ↓
ManagerAgent
    ↓
IntentAgent → QueryOptimizationAgent → YouTubeSearchAgent
    ↓
CandidateRankingAgent → QualityValidationAgent
    ↓
Best video → React Player autoplay
```

Agents communicate with **structured JSON only**. The ManagerAgent uses a plugin-style registry so future agents (TranscriptAgent, PlaylistAgent, RecommendationAgent, etc.) can be registered without changing existing orchestration code.

## Project Structure

```
client/                 React frontend
  components/
  pages/
  hooks/
  services/
  types/
  utils/
server/                 Express API + agents
  agents/
    ManagerAgent.ts
    IntentAgent.ts
    QueryOptimizationAgent.ts
    YouTubeSearchAgent.ts
    CandidateRankingAgent.ts
    QualityValidationAgent.ts
  services/
    GrokService.ts
    YouTubeService.ts
  controllers/
  routes/
  middleware/
  types/
```

## Quick Start

### 1. Install

```bash
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in:

```env
GROK_API_KEY=your_grok_api_key
YOUTUBE_API_KEY=your_youtube_api_key
PORT=3001
CLIENT_ORIGIN=http://localhost:5173
```

Get keys from:

- [xAI Console](https://console.x.ai/) — Grok API
- [Google Cloud Console](https://console.cloud.google.com/) — YouTube Data API v3

### 3. Run

```bash
npm run dev
```

- Frontend: http://localhost:5173
- API: http://localhost:3001

## API

### `POST /api/search`

```json
{
  "description": "Show me a black hole documentary."
}
```

Response:

```json
{
  "videoId": "...",
  "title": "...",
  "channel": "...",
  "description": "...",
  "thumbnail": "...",
  "url": "https://www.youtube.com/watch?v=...",
  "publishedAt": "...",
  "confidence": 92,
  "reason": "Perfect documentary match."
}
```

### `GET /api/health`

Returns service status and registered agents.

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start API + Vite client |
| `npm run build` | Build both workspaces |
| `npm run start` | Start production API |
| `npm run lint` | Lint server and client |
| `npm run format` | Prettier format |

## Agent Responsibilities

| Agent | Role |
| --- | --- |
| **ManagerAgent** | Orchestrates the pipeline; supports plugin spawning |
| **IntentAgent** | Extracts topic, mood, duration, content type, etc. |
| **QueryOptimizationAgent** | Produces 3–5 optimized YouTube queries |
| **YouTubeSearchAgent** | Concurrent search, merge, dedupe |
| **CandidateRankingAgent** | Grok semantic ranking with confidence scores |
| **QualityValidationAgent** | Embeddable / public / confidence > 70; retries up to 3 |

## Extensibility

Register a future agent without rewriting ManagerAgent:

```ts
managerAgent.spawnAgent({
  name: 'plugin:after_intent:TranscriptAgent',
  description: 'Analyze transcripts',
  execute: async (context) => {
    // structured JSON in / out
    return { success: true, message: 'ok', data: {} };
  },
});
```

Plugins named `plugin:after_intent:*` or `plugin:before_return:*` are invoked automatically.

## License

MIT
