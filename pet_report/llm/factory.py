from __future__ import annotations

from pet_report.core.config import get_settings
from pet_report.llm.base import AnswerGenerator
from pet_report.llm.rule_generator import RuleBasedGenerator


def build_generator() -> AnswerGenerator:
    settings = get_settings()
    if settings.llm_provider == "transformers":
        from pet_report.llm.transformers_generator import TransformersGenerator

        return TransformersGenerator()
    return RuleBasedGenerator()
