import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    llm_text_provider: str = os.getenv("LLM_TEXT_PROVIDER", "google_genai")
    llm_text_model: str = os.getenv("LLM_TEXT_MODEL", "gemini-2.5-flash")
    llm_text_stronger_model: str = os.getenv(
        "LLM_TEXT_STRONGER_MODEL", "gemini-2.5-pro"
    )

    llm_vision_provider: str = os.getenv("LLM_VISION_PROVIDER", "google_genai")
    llm_vision_model: str = os.getenv("LLM_VISION_MODEL", "gemini-2.5-flash")
    llm_vision_stronger_model: str = os.getenv(
        "LLM_VISION_STRONGER_MODEL", "gemini-2.5-pro"
    )

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    mistral_api_key: str = os.getenv("MISTRAL_API_KEY", "")
    together_api_key: str = os.getenv("TOGETHER_API_KEY", "")
    fireworks_api_key: str = os.getenv("FIREWORKS_API_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    ollama_base_url: str = os.getenv(
        "OLLAMA_BASE_URL", "http://host.docker.internal:11434"
    )

    firebase_service_account_json: str = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")

    # API / logging
    api_cors_origins: str = os.getenv("API_CORS_ORIGINS", "*")
    log_level: str = os.getenv("LOG_LEVEL", "info")


settings = Settings()
