from pet_report.core.config import get_settings
from pet_report.knowledge.references import ReferenceRangeStore
from pet_report.models.schemas import OcrLine, PetProfile, ReportSource, Species
from pet_report.structuring.parser import ReportStructurer


def test_parse_multiple_metrics_and_flags():
    store = ReferenceRangeStore(get_settings().reference_path)
    structurer = ReportStructurer(store)
    report = structurer.structure(
        [OcrLine(text="犬 血常规 WBC 22.5 10^9/L HGB 95 g/L PLT 80 10^9/L")],
        PetProfile(species=Species.dog),
        ReportSource(source_type="text"),
    )
    by_code = {i.canonical_code: i for i in report.lab_items}
    assert {"WBC", "HGB", "PLT"} <= set(by_code)
    assert by_code["WBC"].flag == "high"
    assert by_code["HGB"].flag == "low"
    assert by_code["PLT"].flag == "low"


def test_unit_conversion_creatinine():
    store = ReferenceRangeStore(get_settings().reference_path)
    report = ReportStructurer(store).structure(
        [OcrLine(text="CREA 2.5 mg/dL BUN 30 mg/dL")],
        PetProfile(species=Species.dog),
        ReportSource(source_type="text"),
    )
    by_code = {i.canonical_code: i for i in report.lab_items}
    assert round(by_code["CREA"].normalized_value, 1) == 221.0
    assert by_code["CREA"].normalized_unit == "umol/L"
    assert by_code["BUN"].normalized_unit == "mmol/L"
