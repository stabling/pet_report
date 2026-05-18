from __future__ import annotations

import json

from pet_report.core.config import get_settings
from pet_report.llm.base import AnswerGenerator
from pet_report.models.schemas import Evidence, LabItem, PetProfile, RiskAlert


class TransformersGenerator(AnswerGenerator):
    def __init__(self) -> None:
        settings = get_settings()
        try:
            from transformers import pipeline
        except Exception as exc:
            raise RuntimeError("transformers backend requires: pip install -e '.[llm]'") from exc
        device = -1 if settings.hf_device == "cpu" else 0
        self.pipe = pipeline(
            "text-generation",
            model=settings.hf_model,
            device=device,
            trust_remote_code=True,
        )
        self.max_new_tokens = settings.hf_max_new_tokens
        self.temperature = settings.hf_temperature
        self.do_sample = settings.hf_do_sample

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
        prompt = self._prompt(summary, abnormal, combos, questions, lab_items, pet_profile, risk_alerts, citations)
        output = self.pipe(
            prompt,
            max_new_tokens=self.max_new_tokens,
            do_sample=self.do_sample,
            temperature=self.temperature,
            return_full_text=False,
        )
        text = output[0].get("generated_text", "").strip() if output else ""
        if not text:
            return summary, abnormal, combos, questions
        # Keep the structured fields from the deterministic engine and only use LLM to refine summary.
        return text[:2000], abnormal, combos, questions

    @staticmethod
    def _prompt(
        summary: str,
        abnormal: list[str],
        combos: list[str],
        questions: list[str],
        lab_items: list[LabItem],
        pet_profile: PetProfile,
        risk_alerts: list[RiskAlert],
        citations: list[Evidence],
    ) -> str:
        payload = {
            "pet_profile": pet_profile.model_dump(mode="json"),
            "lab_items": [i.model_dump(mode="json") for i in lab_items],
            "risk_alerts": [r.model_dump(mode="json") for r in risk_alerts],
            "citations": [c.model_dump(mode="json") for c in citations],
            "draft_summary": summary,
            "abnormal_findings": abnormal,
            "combination_interpretations": combos,
            "recommended_questions": questions,
        }
        return (
            "你是宠物医疗报告解读助手。必须保守、不能诊断、不能开处方。"
            "基于结构化报告和引用证据，用中文输出一段给宠物主人的总结。"
            "如果有急症风险，首先建议线下急诊。不要编造未给出的指标。\n"
            + json.dumps(payload, ensure_ascii=False)
        )
