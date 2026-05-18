from __future__ import annotations

from pet_report.llm.base import AnswerGenerator
from pet_report.models.schemas import Evidence, LabItem, PetProfile, RiskAlert


class RuleBasedGenerator(AnswerGenerator):
    def generate(
        self,
        summary: str,
        abnormal: list[str],
        combos: list[str],
        questions: list[str],
        lab_items: list[LabItem],
        pet_profile: PetProfile,
        risk_alerts: list[RiskAlert],
        citations: list[Evidence],
    ) -> tuple[str, list[str], list[str], list[str]]:
        # Deterministic output is safer for tests and no-GPU environments. It is intentionally conservative.
        return summary, abnormal, combos, questions
