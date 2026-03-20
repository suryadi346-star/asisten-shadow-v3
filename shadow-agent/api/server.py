"""
Shadow Agent — FastAPI REST API
Endpoints untuk Web UI dan CLI integration.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import config
from core.database import (
    init_db, list_sessions, get_session, list_tasks,
    get_task, get_messages, get_stats
)
from core.orchestrator import Orchestrator
from core.provider import check_providers
from agents.agents import AGENT_REGISTRY, get_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shadow.api")

app = FastAPI(
    title=config.app_name,
    version=config.version,
    docs_url="/api/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "web", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.on_event("startup")
def startup():
    init_db()
    logger.info(f"Shadow Agent v{config.version} started")


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RunGoalRequest(BaseModel):
    goal: str
    session_name: Optional[str] = None
    provider: Optional[str] = None  # "anthropic" | "openai" | None

class RunAgentRequest(BaseModel):
    agent_type: str
    prompt: str
    session_id: Optional[str] = None
    provider: Optional[str] = None


# ─── Root → Web UI ────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def root():
    ui_path = os.path.join(os.path.dirname(__file__), "web", "templates", "index.html")
    if os.path.exists(ui_path):
        with open(ui_path) as f:
            return f.read()
    return "<h1>Shadow Agent API Running</h1><a href='/api/docs'>API Docs</a>"


# ─── Health & Status ──────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "version": config.version, "app": config.app_name}

@app.get("/api/providers")
def providers_status():
    return check_providers()

@app.get("/api/agents")
def list_agents():
    return {
        k: {"type": k, "description": cls(session_id="").describe()}
        for k, cls in AGENT_REGISTRY.items()
    }


# ─── Sessions ─────────────────────────────────────────────────────────────────

@app.get("/api/sessions")
def sessions(status: Optional[str] = None):
    return list_sessions(status=status)

@app.get("/api/sessions/{session_id}")
def session_detail(session_id: str):
    s = get_session(session_id)
    if not s:
        raise HTTPException(404, "Session not found")
    tasks = list_tasks(session_id)
    return {**s, "tasks": tasks}


# ─── Tasks ────────────────────────────────────────────────────────────────────

@app.get("/api/tasks/{task_id}")
def task_detail(task_id: str):
    t = get_task(task_id)
    if not t:
        raise HTTPException(404, "Task not found")
    messages = get_messages(task_id)
    return {**t, "messages": messages}


# ─── Run: Full Pipeline ───────────────────────────────────────────────────────

@app.post("/api/run/goal")
def run_goal(req: RunGoalRequest):
    """
    Full pipeline: goal → planner → all agents → result.
    Synchronous — untuk request sederhana.
    """
    progress_log = []

    def on_progress(info):
        progress_log.append(info)
        logger.info(f"[Pipeline] {info}")

    orc = Orchestrator(on_progress=on_progress)
    result = orc.run(
        goal=req.goal,
        session_name=req.session_name,
        provider_override=req.provider,
    )
    result["progress_log"] = progress_log
    return result


@app.post("/api/run/goal/stream")
def run_goal_stream(req: RunGoalRequest):
    """
    Stream progress via Server-Sent Events.
    Frontend bisa listen real-time.
    """
    def event_gen():
        import queue
        q = queue.Queue()

        def on_progress(info):
            q.put(info)

        import threading
        orc = Orchestrator(on_progress=on_progress)

        def run_thread():
            result = orc.run(
                goal=req.goal,
                session_name=req.session_name,
                provider_override=req.provider,
            )
            q.put({"phase": "final_result", **result})
            q.put(None)  # sentinel

        t = threading.Thread(target=run_thread, daemon=True)
        t.start()

        while True:
            item = q.get()
            if item is None:
                break
            yield f"data: {json.dumps(item)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ─── Run: Single Agent ────────────────────────────────────────────────────────

@app.post("/api/run/agent")
def run_agent(req: RunAgentRequest):
    """Jalankan satu agent langsung tanpa pipeline."""
    if req.agent_type not in AGENT_REGISTRY:
        raise HTTPException(400, f"Unknown agent: {req.agent_type}")
    orc = Orchestrator()
    return orc.run_single(
        agent_type=req.agent_type,
        prompt=req.prompt,
        session_id=req.session_id,
        provider=req.provider,
    )


# ─── Stats ────────────────────────────────────────────────────────────────────

@app.get("/api/stats")
def stats():
    return get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
    )
