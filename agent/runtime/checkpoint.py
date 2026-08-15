"""Checkpoint Manager and State Snapshot Abstractions."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, ConfigDict, Field


class CheckpointError(Exception):
    """Base exception for Checkpoint Manager operations."""
    pass


class CheckpointMutationError(CheckpointError):
    """Raised when an attempt is made to mutate an immutable checkpoint."""
    pass


class CheckpointNotFoundError(CheckpointError):
    """Raised when querying a non-existent checkpoint ID."""
    pass


class CheckpointRecord(BaseModel):
    """Immutable, verifiable snapshot record of workspace state."""

    checkpoint_id: str = Field(default_factory=lambda: str(uuid4()))
    workspace_id: str
    session_id: str
    step_index: int
    trigger_action_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_state_ref: str = Field(default="git_head_0000000000000000000000000000000000000000")
    filesystem_state_ref: str = Field(default="fs_merkle_0000000000000000000000000000000000000000")
    postgresql_state_ref: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    integrity_hash: str = Field(default="")
    is_immutable: bool = Field(default=True)

    model_config = ConfigDict(frozen=True)


class WorkspaceStateHasher:
    """Computes SHA-256 Merkle root integrity hash across domain state references."""

    @staticmethod
    def compute_hash(
        git_ref: str,
        fs_ref: str,
        db_ref: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        payload = {
            "git_ref": git_ref,
            "fs_ref": fs_ref,
            "db_ref": db_ref or "",
            "metadata": extra_metadata or {},
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# --- Abstract State Snapshot Provider Interfaces ---

class GitSnapshotProvider(ABC):
    """Abstract interface for Git worktree state snapshotting."""

    @abstractmethod
    async def capture_snapshot(self, workspace_root: str, step_index: int) -> str:
        """Capture Git commit hash or tree ref for workspace."""
        pass


class FilesystemSnapshotProvider(ABC):
    """Abstract interface for Filesystem tree snapshotting."""

    @abstractmethod
    async def capture_snapshot(self, workspace_root: str, step_index: int) -> str:
        """Capture Filesystem pre-image hash or Merkle tree ref."""
        pass


class PostgresSnapshotProvider(ABC):
    """Abstract interface for PostgreSQL database state snapshotting."""

    @abstractmethod
    async def capture_snapshot(self, session_id: str, step_index: int) -> Optional[str]:
        """Capture PostgreSQL savepoint name or snapshot ref."""
        pass


# --- Default Mock Providers for Runtime Testing & Hand-off ---

class MockGitSnapshotProvider(GitSnapshotProvider):
    async def capture_snapshot(self, workspace_root: str, step_index: int) -> str:
        return f"git_commit_step_{step_index}_hash_{uuid4().hex[:8]}"


class MockFilesystemSnapshotProvider(FilesystemSnapshotProvider):
    async def capture_snapshot(self, workspace_root: str, step_index: int) -> str:
        return f"fs_tree_step_{step_index}_hash_{uuid4().hex[:8]}"


class MockPostgresSnapshotProvider(PostgresSnapshotProvider):
    async def capture_snapshot(self, session_id: str, step_index: int) -> Optional[str]:
        return f"rewind_savepoint_step_{step_index}"


class CheckpointManager:
    """Orchestrates domain snapshot providers to manage immutable state checkpoints."""

    def __init__(
        self,
        git_provider: Optional[GitSnapshotProvider] = None,
        fs_provider: Optional[FilesystemSnapshotProvider] = None,
        db_provider: Optional[PostgresSnapshotProvider] = None,
    ) -> None:
        self.git_provider = git_provider or MockGitSnapshotProvider()
        self.fs_provider = fs_provider or MockFilesystemSnapshotProvider()
        self.db_provider = db_provider or MockPostgresSnapshotProvider()
        self._store: Dict[str, CheckpointRecord] = {}

    async def create_checkpoint(
        self,
        session_id: str,
        workspace_id: str,
        step_index: int,
        workspace_root: str,
        trigger_action_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CheckpointRecord:
        """Capture state from all snapshot providers and create an immutable CheckpointRecord."""
        git_ref = await self.git_provider.capture_snapshot(workspace_root, step_index)
        fs_ref = await self.fs_provider.capture_snapshot(workspace_root, step_index)
        db_ref = await self.db_provider.capture_snapshot(session_id, step_index)

        integrity_hash = WorkspaceStateHasher.compute_hash(
            git_ref=git_ref,
            fs_ref=fs_ref,
            db_ref=db_ref,
            extra_metadata=metadata,
        )

        record = CheckpointRecord(
            workspace_id=workspace_id,
            session_id=session_id,
            step_index=step_index,
            trigger_action_id=trigger_action_id,
            git_state_ref=git_ref,
            filesystem_state_ref=fs_ref,
            postgresql_state_ref=db_ref,
            metadata=metadata or {},
            integrity_hash=integrity_hash,
            is_immutable=True,
        )

        self._store[record.checkpoint_id] = record
        return record

    def get_checkpoint(self, checkpoint_id: str) -> CheckpointRecord:
        """Retrieve a CheckpointRecord by ID.
        
        Raises:
            CheckpointNotFoundError: If no checkpoint exists for the given ID.
        """
        if checkpoint_id not in self._store:
            raise CheckpointNotFoundError(f"Checkpoint ID '{checkpoint_id}' not found.")
        return self._store[checkpoint_id]

    def list_checkpoints(self, session_id: str) -> List[CheckpointRecord]:
        """List all checkpoints for a session ordered by step_index."""
        checkpoints = [chk for chk in self._store.values() if chk.session_id == session_id]
        return sorted(checkpoints, key=lambda c: c.step_index)
