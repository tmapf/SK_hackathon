from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Warsaw Property Ideas"
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    database_url: str = "postgresql+psycopg://warsaw:warsaw@localhost:5432/warsaw_ideas"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    session_ttl_hours: int = 12
    turnstile_site_key: str = ""
    turnstile_secret_key: str = ""
    turnstile_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    turnstile_bypass: bool = False
    suggestion_rate_limit_per_hour: int = 10
    login_rate_limit_per_hour: int = 20
    retention_days: int = 365
    sync_cron_hour: int = 3
    sync_cron_minute: int = 0
    # Esri World Street Map — no API key required for standard demo usage.
    tile_url: str = (
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
    )
    tile_attribution: str = (
        "Tiles &copy; Esri &mdash; Source: Esri, DeLorme, NAVTEQ, USGS, "
        "Intermap, iPC, NRCAN, Esri Japan, METI, Esri China (Hong Kong), "
        "Esri (Thailand), TomTom"
    )
    privacy_policy_url: str = "/privacy"
    contact_email: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
