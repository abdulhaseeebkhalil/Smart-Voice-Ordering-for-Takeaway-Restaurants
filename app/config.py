from __future__ import annotations

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Takeaway Order Automation"
    restaurant_name: str = "Sample Takeaway"
    base_url: str = "http://localhost:8000"

    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_tts_model: str = "gpt-4o-mini-tts"
    use_openai_tts: bool = False

    dashboard_password: str = "changeme"
    fallback_forward_number: str = ""

    sqlite_path: str = "sqlite:///./data/orders.db"
    menu_path: str = "./menu.json"
    tax_rate: float = 0.0
    log_level: str = "INFO"

    llm_max_retries: int = 2
    llm_timeout_seconds: int = 30

    printer_mode: str = "dryrun"
    printer_usb_vendor_id: Optional[int] = None
    printer_usb_product_id: Optional[int] = None
    printer_network_host: str = ""
    printer_network_port: int = 9100

    twilio_voice: str = "Polly.Joanna"


settings = Settings()
