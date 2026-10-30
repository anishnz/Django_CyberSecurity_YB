"""Settings + model-config store.

Model settings (display name / base URL / model ID / key) live in
data/model_config.json so the Super Admin can change them at runtime
without redeploying. Everything else comes from environment variables.
"""
import json
import os
import threading
from pathlib import Path

from pydantic import BaseModel

DATA_DIR = Path(os.getenv("RAG_DATA_DIR", "./data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = DATA_DIR / "model_config.json"

# Shared secret between CyberQuest (Django) and this service.
SERVICE_KEY = os.getenv("RAG_SERVICE_KEY", "")
if not SERVICE_KEY:
    raise RuntimeError("RAG_SERVICE_KEY is not set (see .env.example)")

# Embedding model (the chat model cannot do embeddings). Multilingual by default.
EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
# Chunks scoring below this cosine similarity are ignored.
MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.2"))
# Loaded once when the knowledge base is empty, so a new school gets answers straight away.
SEED_FILE = Path(os.getenv("RAG_SEED_FILE", str(Path(__file__).resolve().parent.parent / "cybersecurity_knowledge_base_L0-L6_English.md")))

ROLES = {"student", "teacher", "super_admin"}


# First-start defaults: DeepSeek's public OpenAI-compatible API. The Super Admin can change all of
# them on the Knowledge Base settings page (for example a local Ollama: http://localhost:11434/v1).
# The key can also come from the environment (RAG_LLM_API_KEY) so it never has to be typed twice.
class ModelConfig(BaseModel):
    display_name: str = os.getenv("RAG_LLM_NAME", "DeepSeek")
    base_url: str = os.getenv("RAG_LLM_BASE_URL", "https://api.deepseek.com/v1")
    model_id: str = os.getenv("RAG_LLM_MODEL", "deepseek-chat")
    api_key: str = os.getenv("RAG_LLM_API_KEY", "EMPTY")  # local servers ignore it; DeepSeek needs a real key
    temperature: float = 0.3
    max_tokens: int = 1500
    timeout: int = 120


_lock = threading.Lock()


def load_model_config() -> ModelConfig:
    with _lock:
        if CONFIG_FILE.exists():
            return ModelConfig(**json.loads(CONFIG_FILE.read_text("utf-8")))
    cfg = ModelConfig()
    save_model_config(cfg)
    return cfg


def save_model_config(cfg: ModelConfig) -> None:
    with _lock:
        CONFIG_FILE.write_text(cfg.model_dump_json(indent=2), "utf-8")
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except OSError:
            pass


def public_view(cfg: ModelConfig) -> dict:
    """Config with the API key masked, safe to return to the admin UI."""
    d = cfg.model_dump()
    key = d.pop("api_key")
    d["api_key_masked"] = ("*" * 6 + key[-4:]) if len(key) > 4 else "******"
    return d
