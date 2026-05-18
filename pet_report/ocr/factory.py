from __future__ import annotations

from pet_report.core.config import get_settings
from pet_report.ocr.base import OcrBackend
from pet_report.ocr.text_backend import TextOcrBackend


def build_ocr_backend() -> OcrBackend:
    settings = get_settings()
    if settings.ocr_backend == "text":
        return TextOcrBackend()
    if settings.ocr_backend == "tesseract":
        from pet_report.ocr.tesseract_backend import TesseractOcrBackend

        return TesseractOcrBackend()
    if settings.ocr_backend == "paddleocr":
        from pet_report.ocr.paddle_backend import PaddleOcrBackend

        return PaddleOcrBackend(lang=settings.paddleocr_lang)
    return TextOcrBackend()
