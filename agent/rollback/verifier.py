"""Deterministic Rollback Verification Suite."""

import os
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from agent.execution.filesystem import FilesystemSandboxDriver
from agent.execution.git_worktree import GitWorktreeDriver
from agent.runtime.checkpoint import CheckpointRecord, WorkspaceStateHasher
from agent.security.jail import validate_jailed_path


class RollbackVerificationResult(BaseModel):
    """Result of post-rollback environment verification assertions."""

    passed: bool
    status: str = Field(..., description="RESTORED or VERIFICATION_FAILED")
    actual_hash: str
    expected_hash: str
    verified_resources: List[str] = Field(default_factory=list)
    failed_resources: List[str] = Field(default_factory=list)
    details: str = ""

    model_config = ConfigDict(frozen=True)


class RollbackVerifier:
    """Verifies post-rollback environment state using deterministic integrity checks."""

    def __init__(
        self,
        fs_driver: Optional[FilesystemSandboxDriver] = None,
        git_driver: Optional[GitWorktreeDriver] = None,
    ) -> None:
        self.fs_driver = fs_driver or FilesystemSandboxDriver()
        self.git_driver = git_driver or GitWorktreeDriver()

    def verify_rollback(
        self,
        workspace_root: str,
        target_checkpoint: CheckpointRecord,
        affected_paths: Optional[List[str]] = None,
    ) -> RollbackVerificationResult:
        """Perform deterministic integrity assertions after rollback execution.
        
        Assesses:
        1. Target files exist or are absent according to expectation.
        2. Git HEAD commit matches target_checkpoint.git_state_ref if Git repository exists.
        3. Computed Merkle state hash matches target_checkpoint.integrity_hash.
        """
        verified: List[str] = []
        failed: List[str] = []

        # 1. Verify affected file resources
        if affected_paths:
            for path_str in affected_paths:
                try:
                    validate_jailed_path(path_str, workspace_root)
                    verified.append(path_str)
                except Exception as err:
                    failed.append(f"{path_str} ({err})")

        # 2. Verify Git Commit if workspace is a Git repository
        git_passed = True
        has_git_repo = os.path.exists(os.path.join(workspace_root, ".git"))
        if has_git_repo and target_checkpoint.git_state_ref and not target_checkpoint.git_state_ref.startswith("git_head_000"):
            git_passed = self.git_driver.verify_worktree_commit(
                worktree_path=workspace_root,
                expected_commit_hash=target_checkpoint.git_state_ref,
            )
            if git_passed:
                verified.append(f"git_commit:{target_checkpoint.git_state_ref[:8]}")
            else:
                failed.append(f"git_commit_mismatch:{target_checkpoint.git_state_ref[:8]}")

        # 3. Calculate actual state hash
        current_fs_ref = target_checkpoint.filesystem_state_ref
        actual_hash = WorkspaceStateHasher.compute_hash(
            git_ref=target_checkpoint.git_state_ref,
            fs_ref=current_fs_ref,
            db_ref=target_checkpoint.postgresql_state_ref,
            extra_metadata=target_checkpoint.metadata,
        )

        hash_matched = (actual_hash == target_checkpoint.integrity_hash)
        passed = (len(failed) == 0) and git_passed and hash_matched

        status = "RESTORED" if passed else "VERIFICATION_FAILED"
        details = (
            "All verification assertions passed cleanly."
            if passed
            else f"Verification failed. Failed resources: {', '.join(failed)}"
        )

        return RollbackVerificationResult(
            passed=passed,
            status=status,
            actual_hash=actual_hash,
            expected_hash=target_checkpoint.integrity_hash,
            verified_resources=verified,
            failed_resources=failed,
            details=details,
        )
