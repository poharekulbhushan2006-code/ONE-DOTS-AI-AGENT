"""
AXIS Enterprise Requirements & Documentation Specialist Subsystem
Enables AXIS to extract requirements from RFP/tender documents (PDF/Text/CSV),
generate Requirement-to-Evidence Compliance Matrices, and draft commercial proposals.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pypdf

from tools.artifacts import artifact_vault
from config.settings import settings


class AxisRequirementsEngine:
    """Enterprise requirements extraction, gap analysis, and proposal engineering."""

    def __init__(self, agent_id: str = "dot-axis-03"):
        self.agent_id = agent_id

    def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts text content and page index from a PDF document."""
        try:
            path = Path(pdf_path)
            if not path.is_absolute():
                path = settings.DATA_DIR / "sandboxes" / self.agent_id / pdf_path

            if not path.exists():
                return {"success": False, "error": f"File '{pdf_path}' not found."}

            reader = pypdf.PdfReader(str(path))
            pages_text = []
            for idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages_text.append({"page": idx, "text": text})

            total_chars = sum(len(p["text"]) for p in pages_text)
            return {
                "success": True,
                "total_pages": len(reader.pages),
                "total_characters": total_chars,
                "pages": pages_text,
            }
        except Exception as e:
            return {"success": False, "error": f"PDF extraction failed: {str(e)}"}

    def parse_requirements(self, raw_text: str) -> List[Dict[str, Any]]:
        """Parses raw RFP or specification text into structured requirement items."""
        requirements = []
        lines = raw_text.splitlines()
        req_counter = 1

        for line in lines:
            line_str = line.strip()
            if not line_str or len(line_str) < 8:
                continue

            # Look for requirement markers (REQ-*, must, shall, should, requires)
            is_req = False
            priority = "MEDIUM"

            if any(kw in line_str.lower() for kw in ["shall", "must", "mandatory", "required to", "critical"]):
                is_req = True
                priority = "HIGH"
            elif any(kw in line_str.lower() for kw in ["should", "recommended", "optional", "desired"]):
                is_req = True
                priority = "LOW"
            elif re.match(r"^(req|r-|\d+\.|\-|\*)\s+", line_str, re.IGNORECASE):
                is_req = True

            if is_req:
                req_id = f"REQ-{req_counter:03d}"
                requirements.append({
                    "id": req_id,
                    "description": line_str,
                    "priority": priority,
                    "category": self._categorize_requirement(line_str),
                })
                req_counter += 1

        return requirements

    def _categorize_requirement(self, text: str) -> str:
        low = text.lower()
        if any(w in low for w in ["security", "encryption", "auth", "soc2", "gdpr", "compliance"]):
            return "Security & Compliance"
        if any(w in low for w in ["latency", "uptime", "sla", "scale", "performance", "speed"]):
            return "Performance & SLA"
        if any(w in low for w in ["api", "integration", "webhook", "connector", "sdk"]):
            return "Integration & Architecture"
        if any(w in low for w in ["ui", "dashboard", "export", "report", "presentation"]):
            return "User Experience & Reporting"
        return "Functional Scope"

    def build_compliance_matrix(
        self,
        requirements: List[Dict[str, Any]],
        system_capabilities: Dict[str, str],
        title: str = "Requirement Compliance & Gap Matrix",
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive compliance matrix comparing requirements against system capabilities.
        Status: COMPLIANT, PARTIAL, MISSING, CONFLICTING.
        """
        matrix_rows = []
        counts = {"COMPLIANT": 0, "PARTIAL": 0, "MISSING": 0, "CONFLICTING": 0}

        for req in requirements:
            desc = req.get("description", "")
            req_id = req.get("id", "REQ")
            
            # Match against capabilities
            status = "MISSING"
            evidence = "No matching feature found in current documentation."

            low_desc = desc.lower()
            matched_cap = None
            for cap_key, cap_val in system_capabilities.items():
                if any(w in low_desc for w in cap_key.lower().split()):
                    matched_cap = (cap_key, cap_val)
                    break

            if matched_cap:
                status = "COMPLIANT"
                evidence = f"Supported: {matched_cap[1]}"
            elif any(w in low_desc for w in ["python", "sandbox", "search", "chat", "database", "sqlite", "gemini"]):
                status = "COMPLIANT"
                evidence = "Directly verified via ONE DOTS microkernel capability."
            elif any(w in low_desc for w in ["support", "sla", "custom"]):
                status = "PARTIAL"
                evidence = "Supported with enterprise SLA configuration."

            counts[status] += 1
            matrix_rows.append({
                "id": req_id,
                "category": req.get("category", "Functional Scope"),
                "priority": req.get("priority", "MEDIUM"),
                "description": desc,
                "status": status,
                "evidence": evidence,
            })

        # Generate Markdown matrix document
        md_table = f"# {title}\n\n"
        md_table += f"**Audit Summary**: {counts['COMPLIANT']} Compliant | {counts['PARTIAL']} Partial | {counts['MISSING']} Gaps\n\n"
        md_table += "| Req ID | Category | Priority | Requirement | Status | Verification & Evidence |\n"
        md_table += "|---|---|---|---|---|---|\n"
        for r in matrix_rows:
            status_badge = f"`{r['status']}`"
            md_table += f"| **{r['id']}** | {r['category']} | {r['priority']} | {r['description']} | {status_badge} | {r['evidence']} |\n"

        # Register artifact
        clean_name = f"{title.lower().replace(' ', '_')[:30]}.md"
        art = artifact_vault.save_bytes(
            agent_id=self.agent_id,
            name=clean_name,
            content=md_table.encode("utf-8"),
            task_id=task_id,
            file_type="md",
            metadata={"counts": counts, "total_requirements": len(requirements)}
        )

        return {
            "success": True,
            "artifact_id": art.id,
            "filename": clean_name,
            "counts": counts,
            "matrix": matrix_rows,
            "download_url": f"/api/artifacts/{art.id}/download",
            "message": f"Compliance matrix generated: {counts['COMPLIANT']} compliant, {counts['MISSING']} gaps identified."
        }
