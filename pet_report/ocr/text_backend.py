from __future__ import annotations

from pathlib import Path

from pet_report.models.schemas import OcrLine
from pet_report.ocr.base import OcrBackend


class TextOcrBackend(OcrBackend):
    def extract(self, content: bytes | str | Path, filename: str | None = None) -> list[OcrLine]:
        if isinstance(content, Path):
            raw = content.read_bytes()
        elif isinstance(content, bytes):
            raw = content
        else:
            raw = content.encode("utf-8")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("gb18030", errors="ignore")
        return [OcrLine(text=line.strip(), confidence=1.0) for line in text.splitlines() if line.strip()]
