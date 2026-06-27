"""
Wedding Planner — FastAPI proxy server.

Serves the static HTML and proxies requests to the Anthropic Messages API
so the browser never needs to talk to api.anthropic.com directly (which
avoids CORS issues and keeps the API key on the server).

Run:
    pip install fastapi uvicorn httpx
    export ANTHROPIC_API_KEY=sk-ant-...
    python server.py
Then open http://localhost:8001
"""

import os
import pathlib

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"
HTML_FILE = pathlib.Path(__file__).parent / "wedding-planner.html"

app = FastAPI(title="Wedding Planner Proxy")

# Allow the browser app to call this server from anywhere.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    prompt: str
    model: str | None = None
    max_tokens: int = 1000


@app.get("/")
def index():
    """Serve the front-end."""
    if HTML_FILE.exists():
        return FileResponse(HTML_FILE)
    raise HTTPException(404, "wedding-planner.html not found next to server.py")


@app.get("/health")
def health():
    return {"status": "ok", "key_loaded": bool(os.environ.get("ANTHROPIC_API_KEY"))}


@app.post("/api/agent")
async def run_agent(req: AgentRequest):
    """Proxy a single agent prompt to the Anthropic API and return the JSON text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(500, "Server is missing ANTHROPIC_API_KEY environment variable.")

    payload = {
        "model": req.model or DEFAULT_MODEL,
        "max_tokens": req.max_tokens,
        "messages": [{"role": "user", "content": req.prompt}],
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(ANTHROPIC_URL, json=payload, headers=headers)
    except httpx.RequestError as e:
        raise HTTPException(502, f"Upstream request failed: {e}")

    if res.status_code != 200:
        raise HTTPException(res.status_code, f"Anthropic API error: {res.text}")

    data = res.json()
    text = "".join(b.get("text", "") for b in data.get("content", []))
    return {"text": text, "stop_reason": data.get("stop_reason")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
