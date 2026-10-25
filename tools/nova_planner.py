"""
NOVA Product Launch & Project Manager Subsystem
Enables NOVA to generate structured project roadmaps, track milestone dependencies,
conduct change-impact analysis when scope shifts, and maintain persistent project briefs.
"""

import os
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tools.artifacts import artifact_vault
from config.settings import settings


class NovaProjectPlanner:
    """Project strategy, milestone tracking, and change-impact analysis for NOVA."""

    def __init__(self, agent_id: str = "dot-nova-01"):
        self.agent_id = agent_id

    def create_project_plan(
        self,
        project_name: str,
        goal: str,
        target_deadline: str,
        milestones: List[Dict[str, Any]],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a structured project roadmap with milestones, owners, dependencies, and deliverables.
        """
        plan_doc = {
            "project_name": project_name,
            "goal": goal,
            "target_deadline": target_deadline,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "milestones": milestones,
            "total_milestones": len(milestones),
        }

        # Generate Markdown roadmap
        md_content = f"# 🚀 Project Roadmap: {project_name}\n\n"
        md_content += f"> **Primary Goal**: {goal}\n"
        md_content += f"> **Target Launch**: `{target_deadline}`\n\n"
        md_content += "---\n\n## Milestone Sequence & Work Breakdown\n\n"

        for idx, m in enumerate(milestones, start=1):
            owner = m.get("owner", "NOVA")
            status = m.get("status", "PLANNED")
            deps = ", ".join(m.get("dependencies", [])) or "None"
            md_content += f"### Milestone {idx}: {m.get('title', 'Objective')} (`{status}`)\n"
            md_content += f"- **Owner**: `{owner}`\n"
            md_content += f"- **Target Date**: {m.get('target_date', 'TBD')}\n"
            md_content += f"- **Dependencies**: {deps}\n"
            md_content += f"- **Description**: {m.get('description', '')}\n"
            tasks = m.get("tasks", [])
            if tasks:
                md_content += "- **Tasks**:\n"
                for t in tasks:
                    md_content += f"  - [ ] {t}\n"
            md_content += "\n"

        clean_name = f"{project_name.lower().replace(' ', '_')[:30]}_roadmap.md"
        art = artifact_vault.save_bytes(
            agent_id=self.agent_id,
            name=clean_name,
            content=md_content.encode("utf-8"),
            task_id=task_id,
            file_type="md",
            metadata={"project_name": project_name, "milestone_count": len(milestones)}
        )

        return {
            "success": True,
            "artifact_id": art.id,
            "filename": clean_name,
            "plan": plan_doc,
            "download_url": f"/api/artifacts/{art.id}/download",
            "message": f"Project roadmap for '{project_name}' generated with {len(milestones)} milestones."
        }

    def assess_change_impact(
        self,
        current_plan: Dict[str, Any],
        scope_change_description: str,
        new_deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyzes the impact of a requirement or deadline change on existing milestones,
        identifies affected deliverables, and proposes adjustments while preserving completed work.
        """
        milestones = current_plan.get("milestones", [])
        affected_milestones = []
        unaffected_milestones = []

        low_change = scope_change_description.lower()

        for m in milestones:
            title = m.get("title", "").lower()
            desc = m.get("description", "").lower()
            status = m.get("status", "PLANNED")

            # Preserve completed work
            if status == "COMPLETED":
                unaffected_milestones.append(m)
                continue

            # Check if milestone topics intersect with scope change
            words = [w for w in low_change.split() if len(w) > 4]
            is_affected = any(w in title or w in desc for w in words)
            if new_deadline:
                is_affected = True

            if is_affected:
                adjusted = dict(m)
                adjusted["impact_notes"] = f"Adjusted due to scope change: {scope_change_description}"
                if new_deadline:
                    adjusted["target_date"] = new_deadline
                affected_milestones.append(adjusted)
            else:
                unaffected_milestones.append(m)

        summary_text = (
            f"Scope Change Impact Analysis: {len(affected_milestones)} milestones affected, "
            f"{len(unaffected_milestones)} milestones preserved without disruption. "
            f"Action items updated."
        )

        return {
            "success": True,
            "scope_change": scope_change_description,
            "total_milestones": len(milestones),
            "affected_count": len(affected_milestones),
            "preserved_count": len(unaffected_milestones),
            "affected_milestones": affected_milestones,
            "summary": summary_text,
        }
