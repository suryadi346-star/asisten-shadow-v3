"""
Shadow Agent — AI Provider Layer
Abstraksi tunggal untuk Anthropic & OpenAI.
Fallback otomatis kalau salah satu gagal.
"""
import time
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from config import config

logger = logging.getLogger("shadow.provider")


@dataclass
class AIResponse:
    content: str
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    success: bool
    error: Optional[str] = None


# ─── Anthropic ────────────────────────────────────────────────────────────────

def _call_anthropic(
    system: str,
    messages: list,
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
) -> AIResponse:
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        model = model or config.anthropic_model
        max_tokens = max_tokens or config.max_tokens
        temperature = temperature if temperature is not None else config.temperature

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )
        content = response.content[0].text
        return AIResponse(
            content=content,
            provider="anthropic",
            model=model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            success=True,
        )
    except Exception as e:
        logger.error(f"[Anthropic] Error: {e}")
        return AIResponse(
            content="", provider="anthropic", model=model or config.anthropic_model,
            tokens_in=0, tokens_out=0, success=False, error=str(e)
        )


# ─── OpenAI ───────────────────────────────────────────────────────────────────

def _call_openai(
    system: str,
    messages: list,
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
) -> AIResponse:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=config.openai_api_key)
        model = model or config.openai_model
        max_tokens = max_tokens or config.max_tokens
        temperature = temperature if temperature is not None else config.temperature

        # Format messages: inject system di awal
        full_messages = [{"role": "system", "content": system}] + messages

        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content = response.choices[0].message.content
        usage = response.usage
        return AIResponse(
            content=content,
            provider="openai",
            model=model,
            tokens_in=usage.prompt_tokens,
            tokens_out=usage.completion_tokens,
            success=True,
        )
    except Exception as e:
        logger.error(f"[OpenAI] Error: {e}")
        return AIResponse(
            content="", provider="openai", model=model or config.openai_model,
            tokens_in=0, tokens_out=0, success=False, error=str(e)
        )


# ─── Unified Caller ───────────────────────────────────────────────────────────

def call_ai(
    system: str,
    messages: list,
    provider: str = None,
    model: str = None,
    max_tokens: int = None,
    temperature: float = None,
    agent_type: str = None,
) -> AIResponse:
    """
    Entry point tunggal untuk semua agent.

    Priority:
    1. provider arg (eksplisit)
    2. agent_provider_map[agent_type]
    3. config.default_provider
    4. fallback ke provider lain kalau gagal
    """
    # Tentukan provider
    if not provider:
        if agent_type and agent_type in config.agent_provider_map:
            provider = config.agent_provider_map[agent_type]
        else:
            provider = config.default_provider

    # Validasi API key tersedia
    if provider == "anthropic" and not config.anthropic_api_key:
        logger.warning("Anthropic key kosong, switch ke OpenAI")
        provider = "openai"
    elif provider == "openai" and not config.openai_api_key:
        logger.warning("OpenAI key kosong, switch ke Anthropic")
        provider = "anthropic"

    # Caller map
    callers = {
        "anthropic": _call_anthropic,
        "openai": _call_openai,
    }

    primary_caller = callers.get(provider)
    if not primary_caller:
        return AIResponse(
            content="", provider=provider, model="unknown",
            tokens_in=0, tokens_out=0, success=False,
            error=f"Unknown provider: {provider}"
        )

    # Panggil provider utama (dengan retry)
    for attempt in range(config.max_retries):
        result = primary_caller(system, messages, model, max_tokens, temperature)
        if result.success:
            return result
        if attempt < config.max_retries - 1:
            time.sleep(1.5 ** attempt)  # exponential backoff

    # Fallback ke provider lain
    if config.fallback_enabled:
        fallback = "openai" if provider == "anthropic" else "anthropic"
        fallback_key = (
            config.openai_api_key if fallback == "openai"
            else config.anthropic_api_key
        )
        if fallback_key:
            logger.warning(f"Primary ({provider}) gagal, fallback ke {fallback}")
            fallback_caller = callers[fallback]
            result = fallback_caller(system, messages, None, max_tokens, temperature)
            if result.success:
                result.error = f"Fallback dari {provider}"
                return result

    return result  # Return hasil gagal terakhir


def check_providers() -> dict:
    """Cek status kedua provider."""
    status = {}

    # Test Anthropic
    if config.anthropic_api_key:
        r = _call_anthropic(
            system="Reply with 'OK' only.",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        status["anthropic"] = {"ok": r.success, "model": config.anthropic_model,
                                "error": r.error}
    else:
        status["anthropic"] = {"ok": False, "error": "API key tidak diset"}

    # Test OpenAI
    if config.openai_api_key:
        r = _call_openai(
            system="Reply with 'OK' only.",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        status["openai"] = {"ok": r.success, "model": config.openai_model,
                            "error": r.error}
    else:
        status["openai"] = {"ok": False, "error": "API key tidak diset"}

    return status
