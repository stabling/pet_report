from __future__ import annotations

import tempfile
from pathlib import Path

from pet_report.models.schemas import OcrLine
from pet_report.ocr.base import OcrBackend


class PaddleOcrBackend(OcrBackend):
    def __init__(self, lang: str = "ch") -> None:
        try:
            from paddleocr import PaddleOCR
        except Exception as exc:
            raise RuntimeError("paddleocr is not installed. Run: pip install -e '.[ocr]'") from exc
        self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def extract(self, content: bytes | str | Path, filename: str | None = None) -> list[OcrLine]:
        if isinstance(content, Path):
            path = str(content)
            cleanup = None
        elif isinstance(content, bytes):
            suffix = Path(filename or "upload.png").suffix or ".png"
            f = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            f.write(content)
            f.close()
            path = f.name
            cleanup = Path(path)
        else:
            path = content
            cleanup = None
        try:
            result = self.ocr.ocr(path, cls=True)
        finally:
            if cleanup:
                cleanup.unlink(missing_ok=True)
        lines: list[OcrLine] = []
        for page_idx, page in enumerate(result or []):
            for item in page or []:
                bbox, payload = item
                text, conf = payload
                flat_bbox = [float(v) for pt in bbox for v in pt]
                lines.append(OcrLine(text=str(text).strip(), confidence=float(conf), bbox=flat_bbox, page=page_idx))
        return [line for line in lines if line.text]
