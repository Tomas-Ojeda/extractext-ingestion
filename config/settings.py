from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada del servicio de ingestion (12-factor: config desde entorno)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "extracText Ingestion"
    app_version: str = "0.1.0"
    app_debug: bool = False

    # Consul (service discovery + health checks)
    consul_url: str = "http://consul:8500"
    service_name: str = "ingestion"

    extractor_url: str = "http://pdf-extractxt-extractor:8000"
    storage_url: str = "http://pdf-extractxt-storage:8000"

    # Timeouts de salida, en segundos (factor III)
    extractor_timeout_seconds: int = 30
    storage_timeout_seconds: int = 10


settings = Settings()