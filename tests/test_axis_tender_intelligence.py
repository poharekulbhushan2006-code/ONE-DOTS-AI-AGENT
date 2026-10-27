"""
ONE DOTS - AXIS Tender & Bid Intelligence Test Suite
Verifies:
1. NIT header metadata extraction (Tender ID, Authority, Estimated Cost, EMD, Deadlines, DLP) with page citations.
2. Financial & Technical eligibility criteria extraction (Turnover, Solvency, Similar Works, Statutory).
3. Bidder qualification evaluation (Eligible vs Disqualified gap detection).
4. Markdown Compliance Matrix and Microsoft Word (.docx) Bid Readiness Dossier artifact generation.
5. Dedicated REST API endpoints (/api/tenders/extract, /api/tenders/evaluate, /api/tenders/dossier, /api/tenders/contractor-template).
6. Backward compatibility for generic software/RFP matrices.
"""

import pytest
from fastapi.testclient import TestClient
from api.app import app
from tools.axis_requirements import AxisRequirementsEngine, format_inr
from tools.artifacts import artifact_vault

client = TestClient(app)


SAMPLE_NIT_TEXT = """
[PAGE 1]
GOVERNMENT OF MAHARASHTRA
PUBLIC WORKS DEPARTMENT
OFFICE OF THE EXECUTIVE ENGINEER, PWD DIVISION PUNE
e-Tender Notice No. NIT-2026/PWD/PUNE/HIGHWAY-402
Tender ID: 2026_PWD_88412_1

Name of the Work: Widening and Strengthening of 2-Lane State Highway-42 from Km 12/000 to 34/500 in District Pune.
Estimated Cost of Work: Rs. 18,50,00,000/- (Rupees Eighteen Crores Fifty Lakhs only)
Earnest Money Deposit (EMD): Rs. 37,00,000/- (2% of Estimated Cost)
Cost of Tender Document (Tender Fee): Rs. 10,000/-

[PAGE 2]
TENDER TIMELINE AND SCHEDULE:
1. Document Download Start Date: 01-11-2026 10:00 hrs
2. Pre-Bid Conference Date: 08-11-2026 at 11:30 hrs
3. Last Date and Time for online submission: 22-11-2026 upto 17:00 hrs
4. Date of Technical Bid Opening: 23-11-2026 at 15:00 hrs
5. Time of Completion: 18 (Eighteen) Months
6. Defect Liability Period: 36 Months from actual date of completion
7. Bid Validity: 120 Days from the date of submission

[PAGE 3]
SECTION III: ELIGIBILITY AND QUALIFICATION CRITERIA
Clause 3.1: Enlistment and Registration:
Contractor must be registered in Class I (Civil) or higher with Maharashtra Public Works Department (PWD) or CPWD.

Clause 3.2: Statutory Requirements:
Bidder must possess valid GST registration (GSTIN), active PAN Card, and EPF registration code with latest returns.

Clause 3.4: Affidavit:
Affidavit on non-judicial stamp paper of Rs. 100 confirming that the bidder is not blacklisted or debarred by any State/Central Government Department.

[PAGE 4]
Clause 4.1: Financial Turnover:
The average annual financial turnover of the contractor during the last 3 financial years (FY 2022-23, 2023-24, and 2024-25) shall not be less than 50% of the estimated cost of work.

Clause 4.2: Bank Solvency:
Bidder must submit a Bank Solvency Certificate of minimum 40% of the estimated cost of work issued by any Nationalized or Scheduled Bank dated not older than 6 months.

[PAGE 5]
Clause 5.1: Similar Work Experience:
Experience of having satisfactorily completed similar works during the last 7 years ending last day of month previous to one in which bids are invited:
(a) One similar work of value not less than 80% of estimated cost (Rs. 14.80 Cr), OR
(b) Two similar works each of value not less than 50% of estimated cost (Rs. 9.25 Cr each), OR
(c) Three similar works each of value not less than 40% of estimated cost (Rs. 7.40 Cr each).
Similar work shall mean construction/widening of flexible pavement (bituminous roads) or highway bridges.

Clause 5.2: Plant and Machinery:
Bidder must own or possess legally binding lease agreement for minimum 1 Hot Mix Plant (100-120 TPH), 1 Sensor Paver, and 2 Tandem Rollers.
"""


# ------------------ 1. METADATA EXTRACTION TEST ------------------
def test_axis_tender_metadata_extraction():
    engine = AxisRequirementsEngine()
    meta = engine.extract_tender_metadata(SAMPLE_NIT_TEXT)

    assert meta["tender_id"] in ["NIT-2026/PWD/PUNE/HIGHWAY-402", "2026_PWD_88412_1"]
    assert "public works department" in meta["issuing_authority"].lower() or "pwd" in meta["issuing_authority"].lower()
    assert "Widening and Strengthening" in meta["work_name"]
    assert meta["estimated_cost_inr"] == 185000000.0  # 18.5 Cr
    assert "18.50 Cr" in meta["estimated_cost_raw"]
    assert meta["emd_inr"] == 3700000.0  # 37 Lakhs
    assert "18" in meta["completion_period"]
    assert "36 Months" in meta["defect_liability_period"]
    assert "120 Days" in meta["bid_validity"]

    # Verify page grounding
    citations = meta["page_citations"]
    assert "estimated_cost" in citations
    assert citations["estimated_cost"]["page"] == 1
    assert "18,50,00,000" in citations["estimated_cost"]["snippet"]


# ------------------ 2. ELIGIBILITY CRITERIA EXTRACTION TEST ------------------
def test_axis_eligibility_criteria_extraction():
    engine = AxisRequirementsEngine()
    meta = engine.extract_tender_metadata(SAMPLE_NIT_TEXT)
    criteria = engine.extract_eligibility_criteria(SAMPLE_NIT_TEXT, tender_metadata=meta)

    assert len(criteria) >= 6

    # Verify categories
    categories = {c["category"] for c in criteria}
    assert "Financial" in categories
    assert "Technical" in categories
    assert "Statutory" in categories

    # Verify specific criteria
    turnover_crit = next((c for c in criteria if "turnover" in c["title"].lower()), None)
    assert turnover_crit is not None
    assert turnover_crit["mandatory"] is True
    assert turnover_crit["source_page"] == 4
    assert "Clause 4.1" in turnover_crit["source_clause"]

    solvency_crit = next((c for c in criteria if "solvency" in c["title"].lower()), None)
    assert solvency_crit is not None
    assert solvency_crit["source_page"] == 4

    exp_crit = next((c for c in criteria if "similar" in c["title"].lower() or "experience" in c["title"].lower()), None)
    assert exp_crit is not None
    assert exp_crit["source_page"] == 5


# ------------------ 3. BIDDER QUALIFICATION EVALUATION (QUALIFIED) ------------------
def test_contractor_eligibility_evaluation_compliant():
    engine = AxisRequirementsEngine()
    meta = engine.extract_tender_metadata(SAMPLE_NIT_TEXT)
    criteria = engine.extract_eligibility_criteria(SAMPLE_NIT_TEXT, tender_metadata=meta)

    # Qualified contractor profile exceeding ₹9.25 Cr (50% of 18.5 Cr) turnover & ₹7.4 Cr solvency
    contractor = {
        "company_name": "Sterling Infrastructure Ltd.",
        "contractor_class": "Class I (Civil) PWD Maharashtra",
        "financials": {
            "annual_turnovers": {
                "2022-23": 120000000.0,
                "2023-24": 140000000.0,
                "2024-25": 160000000.0,
            },
            "average_turnover": 140000000.0,  # 14 Cr > 9.25 Cr
            "solvency_amount": 80000000.0,    # 8 Cr > 7.4 Cr
        },
        "past_projects": [
            {
                "name": "Widening of SH-18 Pune",
                "value": 150000000.0,  # 15 Cr > 80% (14.8 Cr)
                "completion_year": 2024,
                "has_completion_cert": True,
            }
        ],
        "statutory": {
            "gst_registered": True,
            "pan_available": True,
            "epf_registered": True,
            "non_blacklisted_affidavit": True,
            "valid_until": "2028-12-31"
        },
        "machinery": ["Hot Mix Plant 120 TPH", "Sensor Paver", "Tandem Rollers"]
    }

    res = engine.evaluate_bidder_eligibility(criteria, contractor, tender_metadata=meta)
    assert res["success"] is True
    assert res["readiness_score"] >= 85.0
    assert res["verdict"] in ["ELIGIBLE_TO_BID", "CONDITIONALLY_ELIGIBLE"]
    assert len(res["critical_shortfalls"]) == 0
    assert res["counts"]["COMPLIANT"] >= 5


# ------------------ 4. BIDDER QUALIFICATION EVALUATION (DISQUALIFIED) ------------------
def test_contractor_eligibility_evaluation_disqualified():
    engine = AxisRequirementsEngine()
    meta = engine.extract_tender_metadata(SAMPLE_NIT_TEXT)
    criteria = engine.extract_eligibility_criteria(SAMPLE_NIT_TEXT, tender_metadata=meta)

    # Under-qualified contractor with small turnover and zero past projects
    contractor = {
        "company_name": "Small Local Builder",
        "contractor_class": "Class IV",
        "financials": {
            "annual_turnovers": {
                "2022-23": 15000000.0,
                "2023-24": 18000000.0,
                "2024-25": 20000000.0,
            },
            "average_turnover": 17666666.0,  # 1.76 Cr << 9.25 Cr required!
            "solvency_amount": 10000000.0,
        },
        "past_projects": [],  # Zero past credentials
        "statutory": {
            "gst_registered": False,
            "pan_available": True,
            "non_blacklisted_affidavit": False,
        },
        "machinery": []
    }

    res = engine.evaluate_bidder_eligibility(criteria, contractor, tender_metadata=meta)
    assert res["success"] is True
    assert res["verdict"] == "DISQUALIFIED_GAPS_IDENTIFIED"
    assert len(res["critical_shortfalls"]) >= 2
    assert any("Turnover" in s for s in res["critical_shortfalls"])


# ------------------ 5. COMPLIANCE MATRIX & WORD DOSSIER ARTIFACTS ------------------
def test_compliance_matrix_and_dossier_docx():
    engine = AxisRequirementsEngine()
    meta = engine.extract_tender_metadata(SAMPLE_NIT_TEXT)
    criteria = engine.extract_eligibility_criteria(SAMPLE_NIT_TEXT, tender_metadata=meta)

    contractor = client.get("/api/tenders/contractor-template").json()

    # 1. Test Markdown matrix generation
    matrix_res = engine.build_compliance_matrix(
        requirements=criteria,
        contractor_profile=contractor,
        title="PWD Highway Tender Compliance Matrix"
    )
    assert matrix_res["success"] is True
    assert matrix_res["artifact_id"] is not None
    assert matrix_res["download_url"].startswith("/api/artifacts/")

    # 2. Test Word .docx dossier generation
    eval_res = engine.evaluate_bidder_eligibility(criteria, contractor, tender_metadata=meta)
    dossier_res = engine.generate_bid_dossier(
        tender_metadata=meta,
        evaluation_result=eval_res,
        contractor_profile=contractor,
        output_filename="test_bid_dossier.docx"
    )
    assert dossier_res["success"] is True
    assert dossier_res["artifact_id"] is not None
    assert dossier_res["filename"] == "test_bid_dossier.docx"

    # Download Word .docx and check binary validity
    dl = client.get(dossier_res["download_url"])
    assert dl.status_code == 200
    assert len(dl.content) > 1000
    assert dl.content.startswith(b"PK\x03\x04")  # Valid DOCX / ZIP magic header!


# ------------------ 6. REST API ENDPOINTS TEST ------------------
def test_tender_api_endpoints():
    # 1. /api/tenders/contractor-template
    tmpl_resp = client.get("/api/tenders/contractor-template")
    assert tmpl_resp.status_code == 200
    profile = tmpl_resp.json()
    assert "company_name" in profile
    assert "financials" in profile

    # 2. /api/tenders/extract
    ext_resp = client.post("/api/tenders/extract", json={"raw_text": SAMPLE_NIT_TEXT})
    assert ext_resp.status_code == 200
    ext_data = ext_resp.json()
    assert ext_data["success"] is True
    assert ext_data["metadata"]["estimated_cost_inr"] > 0
    assert len(ext_data["criteria"]) > 0

    # 3. /api/tenders/evaluate
    eval_resp = client.post("/api/tenders/evaluate", json={
        "raw_text": SAMPLE_NIT_TEXT,
        "contractor_profile": profile
    })
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert "readiness_score" in eval_data
    assert "verdict" in eval_data
    assert len(eval_data["matrix"]) > 0

    # 4. /api/tenders/dossier
    doss_resp = client.post("/api/tenders/dossier", json={
        "tender_metadata": ext_data["metadata"],
        "evaluation_result": eval_data,
        "contractor_profile": profile,
    })
    assert doss_resp.status_code == 200
    doss_data = doss_resp.json()
    assert doss_data["success"] is True
    assert "download_url" in doss_data


# ------------------ 7. BACKWARD COMPATIBILITY TEST ------------------
def test_axis_backward_compatibility():
    engine = AxisRequirementsEngine()
    reqs = engine.parse_requirements("REQ-001: Shall provide isolated sandboxes. REQ-002: Must support SQLite WAL mode.")
    assert len(reqs) == 2
    assert reqs[0]["id"] == "REQ-001"

    matrix = engine.build_compliance_matrix(
        requirements=reqs,
        system_capabilities={"sandboxes": "Dedicated per agent", "sqlite": "WAL mode activated"},
        title="Generic Capabilities Matrix"
    )
    assert matrix["success"] is True
    assert matrix["counts"]["COMPLIANT"] >= 1


# ------------------ 8. DRAG-AND-DROP UPLOAD & BENCHMARK API TESTS ------------------
def test_tender_drag_and_drop_upload_api():
    # Test uploading a real generated benchmark PDF
    from pathlib import Path
    import io
    pdf_path = Path("data/benchmark_tenders/benchmark_01_mahapwd_highway_sh42.pdf")
    assert pdf_path.exists()
    pdf_bytes = pdf_path.read_bytes()

    response = client.post(
        "/api/tenders/upload",
        files={"file": ("tender_notice.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={"generate_dossier": "true"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_pages"] >= 4
    assert data["metadata"]["estimated_cost_inr"] == 185000000.0
    assert len(data["criteria"]) >= 4
    assert data["evaluation"]["readiness_score"] > 0
    assert data["dossier"] is not None
    assert data["dossier"]["download_url"].startswith("/api/artifacts/")
    assert data["dossier"]["filename"].endswith(".docx")


def test_tender_benchmarks_api():
    # Test listing 15 benchmarks
    resp = client.get("/api/tenders/benchmarks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 15
    first_b = data["benchmarks"][0]
    assert "id" in first_b
    assert "work_name" in first_b

    # Test analyzing a benchmark directly
    b_id = first_b["id"]
    a_resp = client.post(f"/api/tenders/benchmarks/{b_id}/analyze", json={})
    assert a_resp.status_code == 200
    a_data = a_resp.json()
    assert a_data["success"] is True
    assert a_data["dossier"]["download_url"].startswith("/api/artifacts/")
    assert a_data["evaluation"]["verdict"] in ["ELIGIBLE_TO_BID", "CONDITIONALLY_ELIGIBLE", "DISQUALIFIED_GAPS_IDENTIFIED"]

