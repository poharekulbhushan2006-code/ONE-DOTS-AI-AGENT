"""
ONE DOTS: Artifact Management Subsystem
Stores, catalogues, and serves verifiable deliverables (PPTX, DOCX, PDF, PNG, CSV, code patches).
"""

import os
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from config.settings import settings
from core.models import ArtifactRecord
from memory.state_store import state_store

ARTIFACTS_DIR = settings.DATA_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


class ArtifactVault:
    def __init__(self):
        self.base_dir = ARTIFACTS_DIR

    def register_file(
        self,
        agent_id: str,
        name: str,
        source_path: Path,
        task_id: Optional[str] = None,
        user_id: str = "usr_owner_default",
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactRecord:
        """Copies or links an artifact file into durable storage and records it."""
        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        ext = source_path.suffix.lstrip(".").lower()
        determined_type = file_type or ext or "bin"
        
        # Unique target name to prevent overwriting
        artifact_id = str(uuid.uuid4())[:8]
        safe_name = f"{artifact_id}_{name}"
        target_path = agent_dir / safe_name

        if source_path.resolve() != target_path.resolve():
            target_path.write_bytes(source_path.read_bytes())

        size = target_path.stat().st_size
        mime, _ = mimetypes.guess_type(str(target_path))
        if not mime:
            mime = "application/octet-stream"

        rec = ArtifactRecord(
            id=artifact_id,
            task_id=task_id,
            agent_id=agent_id,
            user_id=user_id,
            name=name,
            file_type=determined_type,
            file_path=str(target_path.resolve()),
            relative_path=f"{agent_id}/{safe_name}",
            size_bytes=size,
            mime_type=mime,
            metadata=metadata or {},
        )
        return state_store.save_artifact(rec)

    def save_bytes(
        self,
        agent_id: str,
        name: str,
        content: bytes,
        task_id: Optional[str] = None,
        user_id: str = "usr_owner_default",
        file_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactRecord:
        agent_dir = self.base_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(name).suffix.lstrip(".").lower()
        determined_type = file_type or ext or "bin"

        artifact_id = str(uuid.uuid4())[:8]
        safe_name = f"{artifact_id}_{name}"
        target_path = agent_dir / safe_name
        target_path.write_bytes(content)

        size = len(content)
        mime, _ = mimetypes.guess_type(name)
        if not mime:
            mime = "application/octet-stream"

        rec = ArtifactRecord(
            id=artifact_id,
            task_id=task_id,
            agent_id=agent_id,
            user_id=user_id,
            name=name,
            file_type=determined_type,
            file_path=str(target_path.resolve()),
            relative_path=f"{agent_id}/{safe_name}",
            size_bytes=size,
            mime_type=mime,
            metadata=metadata or {},
        )
        return state_store.save_artifact(rec)

    def get_artifact(self, artifact_id: str, user_id: Optional[str] = None, is_admin: bool = False) -> Optional[ArtifactRecord]:
        return state_store.get_artifact(artifact_id, user_id=user_id, is_admin=is_admin)

    def list_artifacts(
        self,
        agent_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_admin: bool = False
    ) -> List[ArtifactRecord]:
        return state_store.list_artifacts(agent_id=agent_id, task_id=task_id, user_id=user_id, is_admin=is_admin)


artifact_vault = ArtifactVault()
