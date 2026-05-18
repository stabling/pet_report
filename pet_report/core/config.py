from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PET_REPORT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "local"
    log_level: str = "INFO"
    data_dir: Path = Path("./runtime_data")
    reference_path: Path = Path("./data/reference_ranges/reference_ranges.yml")
    knowledge_path: Path = Path("./data/knowledge_base/pet_report_knowledge.yml")

    ocr_backend: Literal["text", "tesseract", "paddleocr"] = "text"
    paddleocr_lang: str = "ch"
    ocr_min_confidence: float = Field(default=0.45, ge=0, le=1)

    llm_provider: Literal["rule", "transformers"] = "rule"
    hf_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    hf_device: str = "cpu"
    hf_max_new_tokens: int = 512
    hf_temperature: float = 0.2
    hf_do_sample: bool = False

    enable_risk_gate: bool = True
    enable_rag: bool = True
    require_citations: bool = True
    max_report_size_mb: int = 10
    api_key: str | None = None

    @property
    def max_report_size_bytes(self) -> int:
        return self.max_report_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
