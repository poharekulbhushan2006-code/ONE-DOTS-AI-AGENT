"""
Test Suite for 15 Authentic Benchmark Tenders (Maharashtra PWD, CPWD, NHAI)
Validates calibration of edge-case clause patterns, table layouts, and metadata extraction.
"""

import json
from pathlib import Path
import pytest
from tools.axis_requirements import AxisRequirementsEngine, format_inr


BENCHMARK_DIR = Path("d:/projects/project 1/DOTS AI AGENT/data/benchmark_tenders")


def test_benchmark_catalog_exists():
    manifest_path = BENCHMARK_DIR / "manifest.json"
    assert manifest_path.exists()
    catalog = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(catalog) == 15


@pytest.mark.parametrize("pdf_name", [
    "benchmark_01_mahapwd_highway_sh42.pdf",
    "benchmark_02_mahapwd_bridge_godavari.pdf",
    "benchmark_03_mahapwd_collectorate_pune.pdf",
    "benchmark_04_mahapwd_bulk_water_esr.pdf",
    "benchmark_05_mahapwd_rural_roads_pmgsy.pdf",
    "benchmark_06_cpwd_medical_college_hospital.pdf",
    "benchmark_07_cpwd_residential_colony.pdf",
    "benchmark_08_cpwd_airport_apron_pavement.pdf",
    "benchmark_09_cpwd_heritage_conservation.pdf",
    "benchmark_10_cpwd_national_data_center.pdf",
    "benchmark_11_nhai_greenfield_expressway_ham.pdf",
    "benchmark_12_nhai_elevated_corridor.pdf",
    "benchmark_13_nhai_smart_its_atms.pdf",
    "benchmark_14_nhai_ghat_twin_tunnel.pdf",
    "benchmark_15_nhai_cable_stayed_bridge.pdf",
])
def test_benchmark_tender_extraction(pdf_name):
    engine = AxisRequirementsEngine()
    pdf_path = BENCHMARK_DIR / pdf_name
    assert pdf_path.exists()

    # 1. Test PDF Text Extraction
    text_res = engine.extract_text_from_pdf(str(pdf_path))
    assert text_res["success"] is True
    assert text_res["total_pages"] >= 4
    pages = text_res["pages"]
    assert len(pages) >= 4

    # 2. Test Tender Metadata Extraction
    meta = engine.extract_tender_metadata(pages)
    assert meta["tender_id"] != "NIT-NOT-SPECIFIED"
    assert meta["estimated_cost_inr"] > 0
    assert len(meta["work_name"]) > 10

    # 3. Test Criteria Extraction
    criteria = engine.extract_eligibility_criteria(pages, tender_metadata=meta)
    assert len(criteria) >= 4

    # Verify Financial & Technical Criteria Grounding
    categories = {c["category"] for c in criteria}
    assert "Financial" in categories
    assert "Technical" in categories

    # Verify Page Grounding
    pages_cited = [c["source_page"] for c in criteria if c.get("source_page")]
    assert len(pages_cited) > 0
