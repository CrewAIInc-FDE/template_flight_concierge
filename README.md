# Flight Concierge

An AI-powered travel assistant built with [CrewAI Flows](https://docs.crewai.com), deployed to [CrewAI AMP](https://docs.crewai.com/en/enterprise), with a Flask chat UI that guides users through flight search and booking via conversational human-in-the-loop feedback.

## Architecture

Two independent apps that talk over HTTP:

- **Backend** (`src/flight_concierge/`) — a `FlightConciergeFlow` deployed to AMP. The flow collects location data, drafts a trip plan, requests human approval, searches Google Flights, and emits all messages and feedback requests to the frontend via `DispatcherEventBusService` (HTTP POST to `DISPATCHER_URL`).
- **Frontend** (`frontend/template_flight_concierge_ui/`) — a Flask app. It fires `POST /kickoff` to AMP to start the flow, receives agent events on `/webhook/messages` and feedback requests on `/webhook/feedback`, and streams them to the browser over SSE.

**Request flow:** browser → Flask (`POST /api/start`) → AMP `/kickoff` → flow runs → backend POSTs events to `DISPATCHER_URL` → Flask `/webhook/messages` → SSE → browser → user feedback → Flask `/api/feedback` → AMP callback URL.

## Setup

**Requirements:** Python `>=3.10,<3.14` · [uv](https://docs.astral.sh/uv/) · [ngrok](https://ngrok.com/)

Backend and frontend have **separate** env files:

```bash
cp .env.example .env                   # backend (crew/flow, also set in AMP)
cp frontend/.env.example frontend/.env # frontend (Flask UI)
```

- **Backend `.env`:** `AIRLABS_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, `SERPAPI_API_KEY`, `ARIZE_API_KEY` / `ARIZE_PROJECT_NAME` / `ARIZE_SPACE_ID`, `CREWAI_TRACING_ENABLED`. Set `DISPATCHER_URL` to `https://<your-ngrok-domain>.ngrok.app/webhook/messages` (the public URL where AMP will POST events).
- **Frontend `frontend/.env`:** `CREWAI_ENTERPRISE_URL`, `CREWAI_ENTERPRISE_TOKEN`, `PUBLIC_BASE_URL` (the ngrok URL in dev, your Heroku URL in prod). Dev-only: `PORT` (default `5001`) and `NGROK_DOMAIN`.

Then:

```bash
crewai deploy   # deploy the flow to AMP
bin/start       # installs frontend deps, starts Flask + ngrok on $PORT (default 5001)
```

## Deploying the UI to Heroku

The UI is self-contained in `frontend/` (its own `pyproject.toml` / `uv.lock` — no CrewAI deps). The repo root stays reserved for AMP, so only `frontend/` is deployed via the official `heroku/python` buildpack + `git subtree` (no third-party buildpacks needed).

```bash
# One-time
heroku create <your-ui-app>            # or: heroku git:remote -a <your-ui-app>
heroku buildpacks:set heroku/python -a <your-ui-app>
heroku config:set -a <your-ui-app> \
  CREWAI_ENTERPRISE_URL=... CREWAI_ENTERPRISE_TOKEN=... \
  PUBLIC_BASE_URL=https://<your-ui-app>.herokuapp.com

# Deploy the frontend/ subdirectory (commit first)
git subtree push --prefix frontend heroku main
# If rejected (non-fast-forward):
git push heroku "$(git subtree split --prefix frontend main)":refs/heads/main --force
```

- `PORT` is injected by Heroku — don't set it.
- Run a **single web dyno** (`--workers 1`): SSE state is in-process.
- After deploying, update `DISPATCHER_URL` in your AMP environment to `https://<your-ui-app>.herokuapp.com/webhook/messages`.
