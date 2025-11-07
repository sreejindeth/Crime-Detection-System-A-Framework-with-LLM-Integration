from dataclasses import dataclass
import os


def _env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean flag from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class TelegramSettings:
    bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id_alert: str = os.getenv("TELEGRAM_CHAT_ID_ALERT", "")
    chat_id_report: str = os.getenv("TELEGRAM_CHAT_ID_REPORT", "")
    enable_notifications: bool = _env_flag("TELEGRAM_ENABLED", True)
    send_analysis_progress: bool = _env_flag("TELEGRAM_PROGRESS_NOTIFICATIONS", True)


@dataclass
class LLMSettings:
    # Provider selection: "gemini" or "ollama"
    provider: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    # Gemini API settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # Fast, stable, vision-capable model
    
    # Ollama settings (for fallback)
    enabled: bool = _env_flag("LLM_ENABLED", True)  # Default enabled
    host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llava:7b-v1.5-q4_0")
    
    # Common settings
    timeout: int = int(os.getenv("LLM_TIMEOUT", "120"))
    temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "2"))
    enable_scene_description: bool = _env_flag("LLM_ENABLE_SCENE", True)
    enable_structured_summary: bool = _env_flag("LLM_ENABLE_STRUCTURED", True)
    enable_recommendations: bool = _env_flag("LLM_ENABLE_RECOMMENDATIONS", True)
    enable_reports: bool = _env_flag("LLM_ENABLE_REPORTS", True)
    notify_progress: bool = _env_flag("LLM_NOTIFY_PROGRESS", True)


TELEGRAM_SETTINGS = TelegramSettings()
LLM_SETTINGS = LLMSettings()
