from __future__ import annotations

from pet_report.models.schemas import LabItem, PetProfile, RiskAlert, RiskLevel


class RiskGate:
    URGENT_PATTERNS = {
        "urinary_obstruction": ["尿不出", "尿不出来", "尿闭", "频繁蹲猫砂", "排尿困难", "滴尿"],
        "dyspnea": ["呼吸困难", "张口呼吸", "喘不上气", "舌头发紫", "发绀"],
        "seizure": ["抽搐", "癫痫", "昏迷", "站不稳", "意识不清"],
        "poisoning": ["误食", "中毒", "老鼠药", "巧克力", "葡萄", "百合", "农药"],
        "trauma": ["车祸", "坠楼", "大出血", "严重外伤", "被咬穿"],
    }

    def evaluate(self, chief_complaint: str | None, lab_items: list[LabItem], pet_profile: PetProfile) -> list[RiskAlert]:
        text = chief_complaint or ""
        alerts: list[RiskAlert] = []
        for code, patterns in self.URGENT_PATTERNS.items():
            matched = [p for p in patterns if p in text]
            if matched:
                alerts.append(self._alert_for_pattern(code, matched))

        critical_items = [i for i in lab_items if i.flag in {"critical_low", "critical_high"}]
        if critical_items:
            alerts.append(
                RiskAlert(
                    code="critical_lab",
                    level=RiskLevel.emergency,
                    title="存在危急实验室指标",
                    reason="、".join([f"{i.display_name}={i.normalized_value}{i.normalized_unit or ''}({i.flag})" for i in critical_items]),
                    action="建议尽快联系线下兽医或急诊复查，结合临床表现、补液状态、尿检/影像等进一步判断。",
                    evidence=[i.source_line or i.canonical_code for i in critical_items],
                )
            )

        # Combination: cat urinary symptoms + high CREA/BUN is especially urgent.
        codes = {i.canonical_code: i for i in lab_items}
        if pet_profile.species.value == "cat" and any(p in text for p in self.URGENT_PATTERNS["urinary_obstruction"]):
            if any(c in codes and codes[c].flag in {"high", "critical_high"} for c in ["CREA", "BUN"]):
                alerts.append(
                    RiskAlert(
                        code="feline_urinary_renal_combo",
                        level=RiskLevel.emergency,
                        title="猫排尿异常合并肾指标升高",
                        reason="猫排尿困难/尿闭同时出现肌酐或尿素氮升高，需优先排查尿路梗阻和急性肾损伤。",
                        action="不要在家观察过久，建议立即就近急诊评估膀胱、血钾、肾功能和疼痛状态。",
                        evidence=[codes[c].source_line or c for c in ["CREA", "BUN"] if c in codes],
                    )
                )
        return self._dedupe(alerts)

    @staticmethod
    def _alert_for_pattern(code: str, matched: list[str]) -> RiskAlert:
        mapping = {
            "urinary_obstruction": ("疑似排尿急症", "可能存在尿闭/尿路梗阻风险，尤其猫更需警惕。"),
            "dyspnea": ("呼吸困难风险", "呼吸困难、张口呼吸或发绀属于急症表现。"),
            "seizure": ("神经系统急症风险", "抽搐、昏迷或意识异常需要尽快处理。"),
            "poisoning": ("疑似中毒/误食风险", "误食有毒物或药物可能快速恶化。"),
            "trauma": ("严重外伤风险", "严重外伤或大出血不适合线上观察。"),
        }
        title, reason = mapping[code]
        return RiskAlert(
            code=code,
            level=RiskLevel.emergency,
            title=title,
            reason=f"{reason} 命中关键词：{', '.join(matched)}。",
            action="建议立即联系线下兽医或急诊医院，不要仅依赖线上报告解读。",
            evidence=matched,
        )

    @staticmethod
    def _dedupe(alerts: list[RiskAlert]) -> list[RiskAlert]:
        seen: set[str] = set()
        out: list[RiskAlert] = []
        for alert in alerts:
            if alert.code in seen:
                continue
            seen.add(alert.code)
            out.append(alert)
        return out
