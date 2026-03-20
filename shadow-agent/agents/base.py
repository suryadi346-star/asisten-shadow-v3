"""
Shadow Agent — Base Agent
Semua agent inherit dari sini.
"""
from abc import ABC, abstractmethod
from typing import Optional
from core.provider import call_ai, AIResponse
from core.database import create_task, update_task, save_message, record_stat
from config import config


class BaseAgent(ABC):
    agent_type: str = "base"
    system_prompt: str = "You are a helpful AI assistant."

    def __init__(self, session_id: str, provider: str = None):
        self.session_id = session_id
        self.provider = provider  # None = pakai default dari config map

    def run(self, prompt: str, context: str = "", **kwargs) -> dict:
        """
        Jalankan agent. Return dict dengan result, task_id, dll.
        """
        # Inject context ke prompt kalau ada
        full_prompt = f"{context}\n\n{prompt}".strip() if context else prompt

        messages = [{"role": "user", "content": full_prompt}]

        # Determine model
        provider = self.provider or config.agent_provider_map.get(
            self.agent_type, config.default_provider
        )
        model = (
            config.anthropic_model if provider == "anthropic"
            else config.openai_model
        )

        # Simpan task ke DB
        task_id = create_task(
            session_id=self.session_id,
            agent_type=self.agent_type,
            provider=provider,
            model=model,
            prompt=full_prompt,
        )
        save_message(task_id, "user", full_prompt)

        # Panggil AI
        response: AIResponse = call_ai(
            system=self.system_prompt,
            messages=messages,
            provider=self.provider,
            agent_type=self.agent_type,
            **kwargs
        )

        # Update DB
        if response.success:
            update_task(task_id, response.content, "done", response.tokens_out)
            save_message(task_id, "assistant", response.content)
        else:
            update_task(task_id, response.error or "Failed", "failed")

        # Catat stats
        record_stat(
            provider=response.provider,
            model=response.model,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            success=response.success,
        )

        return {
            "task_id": task_id,
            "agent": self.agent_type,
            "provider": response.provider,
            "model": response.model,
            "success": response.success,
            "result": response.content,
            "tokens": {"in": response.tokens_in, "out": response.tokens_out},
            "error": response.error,
        }

    @abstractmethod
    def describe(self) -> str:
        """Deskripsi singkat agent ini."""
        pass
