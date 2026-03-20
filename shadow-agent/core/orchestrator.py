"""
Shadow Agent — Orchestrator
Satu goal → plan → eksekusi semua agent → output terintegrasi.
"""
import logging
from typing import Optional, Callable
from core.database import create_session, update_session_status, list_tasks
from agents.agents import PlannerAgent, get_agent

logger = logging.getLogger("shadow.orchestrator")


class Orchestrator:
    def __init__(self, on_progress: Optional[Callable] = None):
        """
        on_progress: callback(step_info: dict) untuk streaming progress ke UI.
        """
        self.on_progress = on_progress or (lambda x: None)

    def run(
        self,
        goal: str,
        session_name: str = None,
        provider_override: str = None,
    ) -> dict:
        """
        Full pipeline:
        1. Buat session
        2. Planner breakdown goal → subtasks
        3. Eksekusi tiap subtask dengan agent yang tepat
        4. Return hasil lengkap
        """
        session_name = session_name or f"Session: {goal[:40]}..."
        session_id = create_session(name=session_name, goal=goal)
        self._emit({"phase": "init", "session_id": session_id, "goal": goal})

        # ── Step 1: Planning ──────────────────────────────────────────────────
        self._emit({"phase": "planning", "message": "Analyzing goal..."})
        planner = PlannerAgent(session_id=session_id, provider=provider_override)
        plan_result = planner.plan(goal)

        if not plan_result["success"]:
            update_session_status(session_id, "failed")
            return self._error_result(session_id, "Planner failed", plan_result)

        plan = plan_result.get("plan", {})
        steps = plan.get("plan", []) if plan else []

        if not steps:
            # Planner tidak return JSON valid — fallback ke single researcher+writer
            steps = [
                {"step": 1, "agent": "researcher", "task": goal, "output": "research"},
                {"step": 2, "agent": "writer",     "task": f"Write about: {goal}", "output": "content"},
            ]
            self._emit({"phase": "planning", "message": "Using fallback plan"})
        else:
            self._emit({
                "phase": "planning",
                "message": f"Plan ready: {len(steps)} steps",
                "plan": steps
            })

        # ── Step 2: Execute each step ─────────────────────────────────────────
        results = []
        context = f"Goal: {goal}\n"

        for step in steps:
            step_num  = step.get("step", "?")
            agent_type = step.get("agent", "researcher")
            task_prompt = step.get("task", "")
            expected   = step.get("output", "")

            self._emit({
                "phase": "executing",
                "step": step_num,
                "agent": agent_type,
                "task": task_prompt[:80],
            })

            try:
                agent = get_agent(
                    agent_type=agent_type,
                    session_id=session_id,
                    provider=provider_override,
                )
                result = agent.run(prompt=task_prompt, context=context)
            except ValueError as e:
                # Agent type tidak dikenal → skip
                logger.warning(f"Unknown agent '{agent_type}' at step {step_num}: {e}")
                result = {"success": False, "error": str(e), "result": ""}

            result["step"] = step_num
            result["expected_output"] = expected
            results.append(result)

            if result["success"]:
                # Tambah hasil ke context untuk step berikutnya
                context += f"\n[Step {step_num} - {agent_type}]:\n{result['result'][:500]}\n"
                self._emit({
                    "phase": "step_done",
                    "step": step_num,
                    "agent": agent_type,
                    "preview": result["result"][:120] + "...",
                })
            else:
                self._emit({
                    "phase": "step_failed",
                    "step": step_num,
                    "error": result.get("error"),
                })

        # ── Step 3: Selesai ───────────────────────────────────────────────────
        success_count = sum(1 for r in results if r.get("success"))
        status = "done" if success_count > 0 else "failed"
        update_session_status(session_id, status)

        total_tokens = sum(
            r.get("tokens", {}).get("out", 0) for r in results
        )

        self._emit({
            "phase": "complete",
            "session_id": session_id,
            "steps_done": success_count,
            "steps_total": len(results),
            "total_tokens": total_tokens,
        })

        return {
            "session_id": session_id,
            "goal": goal,
            "status": status,
            "plan": steps,
            "results": results,
            "summary": {
                "steps_done": success_count,
                "steps_total": len(results),
                "total_tokens": total_tokens,
            }
        }

    def run_single(
        self,
        agent_type: str,
        prompt: str,
        session_id: str = None,
        provider: str = None,
    ) -> dict:
        """Jalankan satu agent tanpa full pipeline."""
        if not session_id:
            session_id = create_session(
                name=f"Single: {agent_type}",
                goal=prompt[:100]
            )
        agent = get_agent(agent_type=agent_type, session_id=session_id, provider=provider)
        return agent.run(prompt=prompt)

    def _emit(self, info: dict):
        try:
            self.on_progress(info)
        except Exception:
            pass

    def _error_result(self, session_id: str, message: str, detail: dict) -> dict:
        return {
            "session_id": session_id,
            "status": "failed",
            "error": message,
            "detail": detail,
        }
