"""
Shadow Agent — 4 Core Agents
Planner | Researcher | Writer | Coder
"""
from agents.base import BaseAgent


# ─── Planner ──────────────────────────────────────────────────────────────────

class PlannerAgent(BaseAgent):
    agent_type = "planner"
    system_prompt = """You are a strategic Planner AI. Your job:
1. Analyze the user's goal
2. Break it into clear, ordered subtasks
3. Assign each subtask to the right agent type: [planner, researcher, writer, coder]
4. Output as JSON:
{
  "goal_summary": "...",
  "plan": [
    {"step": 1, "agent": "researcher", "task": "...", "output": "expected output"},
    {"step": 2, "agent": "writer",     "task": "...", "output": "..."},
    ...
  ],
  "estimated_steps": N
}
Be concise. No fluff. Focus on execution."""

    def describe(self) -> str:
        return "Breaks goals into ordered subtasks and assigns them to agents."

    def plan(self, goal: str) -> dict:
        """Convenience wrapper — returns plan dict."""
        import json
        result = self.run(prompt=f"Goal: {goal}")
        if result["success"]:
            try:
                # Parse JSON dari response
                content = result["result"]
                # Strip markdown code fences kalau ada
                if "```" in content:
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                plan = json.loads(content.strip())
                result["plan"] = plan
            except json.JSONDecodeError:
                result["plan"] = None
                result["raw_plan"] = result["result"]
        return result


# ─── Researcher ───────────────────────────────────────────────────────────────

class ResearcherAgent(BaseAgent):
    agent_type = "researcher"
    system_prompt = """You are a Research AI. Your job:
1. Take a research topic or question
2. Provide a structured, fact-dense summary
3. Format output as:
   ## Key Findings
   - ...
   ## Details
   ...
   ## Sources / References (if applicable)
   ...
   ## Gaps / Unknowns
   ...

Be accurate. Flag uncertainty explicitly. No padding."""

    def describe(self) -> str:
        return "Researches topics and returns structured, fact-dense summaries."


# ─── Writer ───────────────────────────────────────────────────────────────────

class WriterAgent(BaseAgent):
    agent_type = "writer"
    system_prompt = """You are a Writer AI. Your job:
1. Receive a content brief (topic, tone, format, audience)
2. Produce high-quality written content
3. Match tone precisely: technical, casual, persuasive, narrative, etc.
4. Structure output clearly with headers if needed

Output ready-to-use content. No meta-commentary about your writing."""

    def describe(self) -> str:
        return "Generates written content from briefs — articles, docs, copy, etc."


# ─── Coder ────────────────────────────────────────────────────────────────────

class CoderAgent(BaseAgent):
    agent_type = "coder"
    system_prompt = """You are a Coder AI. Your job:
1. Receive a coding task or bug
2. Write clean, working, well-commented code
3. Use the language/framework specified, default to Python if unspecified
4. Format output:
   ```language
   [code here]
   ```
   **Explanation:** brief explanation of the approach
   **Usage:** how to run/use it
   **Notes:** edge cases or limitations

Write production-quality code. No placeholder logic."""

    def describe(self) -> str:
        return "Writes and debugs code in any language."


# ─── Agent Registry ───────────────────────────────────────────────────────────

AGENT_REGISTRY = {
    "planner":    PlannerAgent,
    "researcher": ResearcherAgent,
    "writer":     WriterAgent,
    "coder":      CoderAgent,
}


def get_agent(agent_type: str, session_id: str, provider: str = None) -> BaseAgent:
    """Factory function — ambil agent by type."""
    cls = AGENT_REGISTRY.get(agent_type)
    if not cls:
        raise ValueError(f"Unknown agent type: {agent_type}. Valid: {list(AGENT_REGISTRY)}")
    return cls(session_id=session_id, provider=provider)
