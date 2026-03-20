"""
Shadow Agent — Central Config
"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Config:
    # === AI Providers ===
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Default models
    anthropic_model: str = "claude-3-5-haiku-20241022"   # ringan & cepat
    openai_model: str = "gpt-4o-mini"                    # murah & cepat

    # Fallback order: coba provider utama, kalau gagal pakai backup
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "anthropic")  # "anthropic" | "openai"
    fallback_enabled: bool = True

    # === App ===
    app_name: str = "Shadow Agent"
    version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # === Database ===
    db_path: str = os.getenv("DB_PATH", "data/shadow.db")

    # === Web Server ===
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5000"))

    # === Agent Settings ===
    max_tokens: int = 2048
    temperature: float = 0.7
    max_retries: int = 2

    # === Agent → Provider mapping (per-agent override) ===
    agent_provider_map: dict = field(default_factory=lambda: {
        "planner":    "anthropic",   # Claude lebih baik untuk reasoning
        "researcher": "openai",      # GPT cukup untuk summarize
        "writer":     "anthropic",   # Claude lebih baik untuk nulis
        "coder":      "anthropic",   # Claude lebih baik untuk code
    })

config = Config()
