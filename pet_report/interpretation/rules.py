from __future__ import annotations

from pet_report.models.schemas import Evidence, LabItem, PetProfile, RiskAlert


class RuleInterpreter:
    def build(
        self,
        lab_items: list[LabItem],
        pet_profile: PetProfile,
        chief_complaint: str | None,
        risk_alerts: list[RiskAlert],
        citations: list[Evidence],
    ) -> tuple[str, list[str], list[str], list[str]]:
        abnormal = self._abnormal_findings(lab_items)
        combos = self._combination_interpretations(lab_items, pet_profile)
        questions = self._recommended_questions(lab_items, chief_complaint)

        if risk_alerts:
            summary = "报告中存在需要优先处理的风险信号。建议先按急症/线下复诊路径处理，再结合完整报告和临床症状继续解释。"
        elif abnormal:
            summary = "报告已结构化完成，发现部分异常指标。以下解读基于默认参考区间和本地知识库证据，应结合医院原始参考范围、症状和兽医体检判断。"
        else:
            summary = "报告已结构化完成，已识别指标大多处于参考范围内。若症状持续，仍建议结合体检、影像或复查判断。"

        if citations:
            summary += f" 本次回答引用了 {len(citations)} 条知识证据。"
        return summary, abnormal, combos, questions

    @staticmethod
    def _abnormal_findings(lab_items: list[LabItem]) -> list[str]:
        findings: list[str] = []
        for item in lab_items:
            if item.flag in {"high", "critical_high"}:
                ref = item.reference_range
                ref_text = f"，参考 {ref.low}-{ref.high}{ref.unit}" if ref else ""
                findings.append(f"{item.display_name}升高：{item.normalized_value}{item.normalized_unit or ''}{ref_text}。")
            elif item.flag in {"low", "critical_low"}:
                ref = item.reference_range
                ref_text = f"，参考 {ref.low}-{ref.high}{ref.unit}" if ref else ""
                findings.append(f"{item.display_name}降低：{item.normalized_value}{item.normalized_unit or ''}{ref_text}。")
        return findings

    @staticmethod
    def _combination_interpretations(lab_items: list[LabItem], pet_profile: PetProfile) -> list[str]:
        by_code = {i.canonical_code: i for i in lab_items}
        combos: list[str] = []
        if any(c in by_code and by_code[c].flag in {"high", "critical_high"} for c in ["CREA", "BUN"]):
            if all(c in by_code and by_code[c].flag in {"high", "critical_high"} for c in ["CREA", "BUN"]):
                combos.append("肌酐与尿素氮同时升高：需要结合饮水、脱水、尿量、尿检和影像判断肾前性脱水、肾脏损伤或泌尿道梗阻等可能。")
            else:
                combos.append("肾功能相关指标有异常：建议结合尿检、SDMA、尿量变化和复查趋势判断，单项指标不能直接确诊。")
        if any(c in by_code and by_code[c].flag in {"high", "critical_high"} for c in ["ALT", "AST", "ALP"]):
            combos.append("肝酶/胆汁淤积相关指标升高：可能与肝胆问题、药物、炎症、应激或肌肉损伤有关，应结合胆红素、GGT、影像和用药史。")
        if "WBC" in by_code and by_code["WBC"].flag in {"high", "critical_high"}:
            combos.append("白细胞升高：提示炎症、感染、应激或激素影响等可能，需要结合分类计数、体温、疼痛和影像判断。")
        if any(c in by_code and by_code[c].flag in {"low", "critical_low"} for c in ["RBC", "HGB"]):
            combos.append("红细胞/血红蛋白降低：提示贫血可能，建议观察牙龈颜色、黑便、出血点、精神和呼吸状态，并与兽医讨论进一步检查。")
        if "PLT" in by_code and by_code["PLT"].flag in {"low", "critical_low"}:
            combos.append("血小板降低：需关注出血风险，也要排除采血凝集或仪器误差，必要时做血涂片复核。")
        if "GLU" in by_code and by_code["GLU"].flag in {"low", "critical_low"}:
            combos.append("血糖降低：若伴随虚弱、抽搐或意识异常属于高风险情况，应尽快就医。")
        if "GLU" in by_code and by_code["GLU"].flag in {"high", "critical_high"}:
            combos.append("血糖升高：需结合应激、饮食、尿糖/酮体、饮水排尿变化评估，不宜仅凭一次血糖判断糖尿病。")
        return combos

    @staticmethod
    def _recommended_questions(lab_items: list[LabItem], chief_complaint: str | None) -> list[str]:
        codes = {i.canonical_code for i in lab_items}
        questions = ["请确认报告是否为同一家医院/同一设备的参考范围，并尽量提供原图。"]
        if {"CREA", "BUN"} & codes:
            questions.append("最近饮水、排尿量、尿色、是否呕吐或脱水？是否做过尿检/SDMA/影像？")
        if {"ALT", "AST", "ALP"} & codes:
            questions.append("近期是否用药、驱虫、麻醉、吃过异常食物？是否有黄疸、腹痛或食欲下降？")
        if {"WBC", "HGB", "PLT"} & codes:
            questions.append("是否发热、疼痛、牙龈苍白、黑便、皮下出血点或近期外伤？")
        if not chief_complaint:
            questions.append("请补充主诉：症状持续多久、精神食欲、大小便、用药和既往病史。")
        return questions
