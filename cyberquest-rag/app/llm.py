"""Thin client for an OpenAI-compatible chat endpoint (vLLM / SGLang / Ollama ...)."""
import re

from openai import OpenAI

from .config import load_model_config

# Some reasoning models put their chain of thought inside <think> tags.
_THINK = re.compile(r"<think>.*?</think>", re.S)


def chat(messages: list[dict], **overrides) -> str:
    # Config is re-read on every call, so Super Admin changes apply immediately.
    cfg = load_model_config()
    client = OpenAI(base_url=cfg.base_url, api_key=cfg.api_key, timeout=cfg.timeout)
    resp = client.chat.completions.create(
        model=cfg.model_id,
        messages=messages,
        temperature=overrides.get("temperature", cfg.temperature),
        max_tokens=overrides.get("max_tokens", cfg.max_tokens),
    )
    text = resp.choices[0].message.content or ""
    return _THINK.sub("", text).strip()
