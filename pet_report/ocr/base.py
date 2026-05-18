from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pet_report.models.schemas import OcrLine


class OcrBackend(ABC):
    @abstractmethod
    def extract(self, content: bytes | str | Path, filename: str | None = None) -> list[OcrLine]:
        raise NotImplementedError
