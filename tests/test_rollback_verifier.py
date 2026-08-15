import pytest

from agent.rollback.verifier import RollbackVerifier
from agent.runtime.checkpoint import CheckpointRecord, WorkspaceStateHasher


def test_rollback_verifier_passed(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Pre-create test file
    test_file = workspace / "src" / "app.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("print('restored')")

    git_ref = "git_head_0000000000000000000000000000000000000000"
    fs_ref = "fs_merkle_123"
    integrity_hash = WorkspaceStateHasher.compute_hash(git_ref, fs_ref)

    chk = CheckpointRecord(
        workspace_id="ws-1",
        session_id="sess-1",
        step_index=1,
        git_state_ref=git_ref,
        filesystem_state_ref=fs_ref,
        integrity_hash=integrity_hash,
    )

    verifier = RollbackVerifier()
    res = verifier.verify_rollback(
        workspace_root=str(workspace),
        target_checkpoint=chk,
        affected_paths=["src/app.py"],
    )

    assert res.passed is True
    assert res.status == "RESTORED"
    assert res.actual_hash == integrity_hash


def test_rollback_verifier_hash_mismatch(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    chk = CheckpointRecord(
        workspace_id="ws-1",
        session_id="sess-1",
        step_index=1,
        git_state_ref="git_head_0000000000000000000000000000000000000000",
        filesystem_state_ref="fs_merkle_123",
        integrity_hash="tampered_expected_hash",  # Wrong hash
    )

    verifier = RollbackVerifier()
    res = verifier.verify_rollback(
        workspace_root=str(workspace),
        target_checkpoint=chk,
    )

    assert res.passed is False
    assert res.status == "VERIFICATION_FAILED"
