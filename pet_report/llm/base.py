from __future__ import annotations

from abc import ABC, abstractmethod

from pet_report.models.schemas import Evidence, LabItem, PetProfile, RiskAlert


class AnswerGenerator(ABC):
    @abstractmethod
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
        raise NotImplementedError
