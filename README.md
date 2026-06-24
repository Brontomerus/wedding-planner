# Wedding Planner — Agentic Workflow

A browser-based wedding planning tool that runs multiple AI agents in parallel to research venues, catering, officiants, photography, and music for your wedding — then synthesizes everything into a master checklist.

Each agent is a specialized Claude prompt that returns structured JSON. The frontend renders results into cards with tags, cost breakdowns, and actionable tips tailored to your location and budget.

## Architecture

```
Browser (wedding-planner.html)
   │
   ├─ Venue agent ──────┐
   ├─ Catering agent ────┤
   ├─ Officiant agent ───┼──► Claude API (via FastAPI proxy)
   ├─ Photography agent ──┤
   ├─ Music agent ────────┘
   │
   └─ Checklist agent ──────► Synthesizes all results into a timeline
```

- **`server.py`** — FastAPI proxy that serves the HTML and forwards requests to the Anthropic Messages API, keeping the API key server-side and avoiding CORS issues.
- **`wedding-planner.html`** — Single-page frontend with agent selection, config inputs, and result rendering.

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

## Run locally

```bash
pip install fastapi uvicorn httpx

export ANTHROPIC_API_KEY=sk-ant-...   # Linux/macOS
set ANTHROPIC_API_KEY=sk-ant-...      # Windows cmd
$env:ANTHROPIC_API_KEY = "sk-ant-..." # PowerShell

python server.py
```

Open [http://localhost:8000](http://localhost:8000). Enter your wedding details, select which agents to run, and click **Run all agents**.

## Configuration

| Field | Default | Description |
|-------|---------|-------------|
| Search area | Reno, NV region | Geographic area for vendor search |
| Guest count | 140 | Determines venue capacity and catering estimates |
| Total budget | $35,000 | Split across all vendor categories |
| Preferred dates | May–June / Late Aug–Sept 2027 | Affects availability tips and heat warnings |

## Known limitations

- The frontend currently calls the Anthropic API directly from the browser instead of routing through the proxy server (CORS will block this).
- Agents run sequentially — independent agents could run in parallel.
- The checklist agent doesn't receive results from other agents, so it can't synthesize a unified plan.
- JSON parsing is fragile with no retry logic.
