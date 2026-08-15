import pytest
from pydantic import ValidationError

from agent.runtime.checkpoint import (
    CheckpointManager,
    CheckpointNotFoundError,
    WorkspaceStateHasher,
)


@pytest.mark.asyncio
async def test_checkpoint_creation_and_retrieval(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    manager = CheckpointManager()

    record = await manager.create_checkpoint(
        session_id="sess-123",
        workspace_id="ws-456",
        step_index=1,
        workspace_root=str(workspace),
        trigger_action_id="act-789",
        metadata={"reason": "pre_step_checkpoint"},
    )

    assert record.session_id == "sess-123"
    assert record.step_index == 1
    assert record.trigger_action_id == "act-789"
    assert record.git_state_ref.startswith("git_commit_step_1")
    assert record.filesystem_state_ref.startswith("fs_tree_step_1")
    assert record.postgresql_state_ref == "rewind_savepoint_step_1"
    assert len(record.integrity_hash) == 64  # SHA-256 hash length

    retrieved = manager.get_checkpoint(record.checkpoint_id)
    assert retrieved == record


@pytest.mark.asyncio
async def test_checkpoint_listing(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    manager = CheckpointManager()

    chk1 = await manager.create_checkpoint("sess-1", "ws-1", 1, str(workspace))
    chk3 = await manager.create_checkpoint("sess-1", "ws-1", 3, str(workspace))
    chk2 = await manager.create_checkpoint("sess-1", "ws-1", 2, str(workspace))

    checkpoints = manager.list_checkpoints("sess-1")
    assert len(checkpoints) == 3
    assert [c.step_index for c in checkpoints] == [1, 2, 3]


def test_unknown_checkpoint_raises_error():
    manager = CheckpointManager()
    with pytest.raises(CheckpointNotFoundError):
        manager.get_checkpoint("nonexistent-id")


@pytest.mark.asyncio
async def test_checkpoint_immutability(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    manager = CheckpointManager()

    record = await manager.create_checkpoint("sess-1", "ws-1", 1, str(workspace))

    with pytest.raises(ValidationError):
        record.git_state_ref = "tampered_hash"  # Pydantic frozen model enforces immutability


def test_workspace_state_hasher():
    hash1 = WorkspaceStateHasher.compute_hash("git1", "fs1", "db1")
    hash2 = WorkspaceStateHasher.compute_hash("git1", "fs1", "db1")
    hash3 = WorkspaceStateHasher.compute_hash("git2", "fs1", "db1")

    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64
