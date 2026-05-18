from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image

from pet_report.models.schemas import OcrLine
from pet_report.ocr.base import OcrBackend


class TesseractOcrBackend(OcrBackend):
    def __init__(self, lang: str = "chi_sim+eng") -> None:
        self.lang = lang
        try:
            import pytesseract  # noqa: F401
        except Exception as exc:
            raise RuntimeError("pytesseract is not installed. Run: pip install -e '.[ocr]' and install system tesseract") from exc

    def extract(self, content: bytes | str | Path, filename: str | None = None) -> list[OcrLine]:
        import pytesseract

        if isinstance(content, Path):
            image = Image.open(content)
        elif isinstance(content, bytes):
            image = Image.open(BytesIO(content))
        else:
            image = Image.open(content)
        data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
        lines: list[OcrLine] = []
        for i, text in enumerate(data.get("text", [])):
            text = text.strip()
            if not text:
                continue
            conf_raw = data.get("conf", ["-1"])[i]
            try:
                conf = max(0.0, min(1.0, float(conf_raw) / 100.0))
            except Exception:
                conf = 0.0
            bbox = [float(data["left"][i]), float(data["top"][i]), float(data["width"][i]), float(data["height"][i])]
            lines.append(OcrLine(text=text, confidence=conf, bbox=bbox))
        return lines
