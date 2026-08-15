"""Filesystem Sandbox Execution & Pre-Image Snapshot Driver."""

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from agent.runtime.contracts import ActionResult, InverseOperationReference
from agent.security.jail import validate_jailed_path


class FilesystemDriverError(Exception):
    """Base exception for Filesystem Sandbox Driver operations."""
    pass


class PreimageNotFoundError(FilesystemDriverError):
    """Raised when attempting to restore a non-existent pre-image hash."""
    pass


class FilesystemSandboxDriver:
    """Executes filesystem tool operations inside jailed paths and manages pre-image snapshots."""

    def __init__(self, snapshot_dir: Optional[str] = None) -> None:
        self._preimages: Dict[str, Optional[bytes]] = {}  # hash -> bytes or None (non-existence)
        self.snapshot_dir = snapshot_dir

    def _compute_hash(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def capture_preimage(self, target_path: str, workspace_root: str) -> Tuple[Optional[str], bool]:
        """Capture pre-execution image of a target file.
        
        Returns:
            Tuple of (preimage_hash, exists_flag). If file did not exist, preimage_hash is None.
        """
        canonical_path = validate_jailed_path(target_path, workspace_root)
        if not os.path.exists(canonical_path):
            return None, False

        with open(canonical_path, "rb") as f:
            content = f.read()

        file_hash = self._compute_hash(content)
        self._preimages[file_hash] = content
        return file_hash, True

    def create_file(self, target_path: str, content: str, workspace_root: str) -> ActionResult:
        """Create a new file within the jailed workspace."""
        canonical_path = validate_jailed_path(target_path, workspace_root)
        if os.path.exists(canonical_path):
            return ActionResult(
                success=False,
                error_message=f"File '{target_path}' already exists; use write_file to overwrite.",
            )

        os.makedirs(os.path.dirname(canonical_path), exist_ok=True)
        with open(canonical_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ActionResult(
            success=True,
            output={"path": target_path, "bytes_written": len(content.encode("utf-8"))},
        )

    def write_file(self, target_path: str, content: str, workspace_root: str) -> ActionResult:
        """Write content to a file inside the jailed workspace."""
        canonical_path = validate_jailed_path(target_path, workspace_root)
        os.makedirs(os.path.dirname(canonical_path), exist_ok=True)

        with open(canonical_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ActionResult(
            success=True,
            output={"path": target_path, "bytes_written": len(content.encode("utf-8"))},
        )

    def delete_file(self, target_path: str, workspace_root: str) -> ActionResult:
        """Delete a file inside the jailed workspace."""
        canonical_path = validate_jailed_path(target_path, workspace_root)
        if not os.path.exists(canonical_path):
            return ActionResult(
                success=False,
                error_message=f"File '{target_path}' does not exist.",
            )

        os.remove(canonical_path)
        return ActionResult(
            success=True,
            output={"path": target_path, "deleted": True},
        )

    def move_file(self, source_path: str, destination_path: str, workspace_root: str) -> ActionResult:
        """Move/rename a file inside the jailed workspace."""
        canonical_src = validate_jailed_path(source_path, workspace_root)
        canonical_dest = validate_jailed_path(destination_path, workspace_root)

        if not os.path.exists(canonical_src):
            return ActionResult(
                success=False,
                error_message=f"Source path '{source_path}' does not exist.",
            )

        os.makedirs(os.path.dirname(canonical_dest), exist_ok=True)
        shutil.move(canonical_src, canonical_dest)
        return ActionResult(
            success=True,
            output={"source": source_path, "destination": destination_path},
        )

    def restore_preimage(
        self,
        target_path: str,
        preimage_hash: Optional[str],
        workspace_root: str,
    ) -> bool:
        """Restore target file to exact pre-image state or delete if file originally did not exist."""
        canonical_path = validate_jailed_path(target_path, workspace_root)

        # Case 1: File originally did not exist -> Delete created file
        if preimage_hash is None:
            if os.path.exists(canonical_path):
                os.remove(canonical_path)
            return True

        # Case 2: Restore pre-image content
        if preimage_hash not in self._preimages:
            raise PreimageNotFoundError(f"Preimage hash '{preimage_hash}' not found in store.")

        content_bytes = self._preimages[preimage_hash]
        os.makedirs(os.path.dirname(canonical_path), exist_ok=True)
        with open(canonical_path, "wb") as f:
            f.write(content_bytes)

        # Verify restored content hash matches preimage_hash
        with open(canonical_path, "rb") as f:
            restored_hash = self._compute_hash(f.read())

        if restored_hash != preimage_hash:
            raise FilesystemDriverError(
                f"Restored file hash '{restored_hash}' does not match expected preimage hash '{preimage_hash}'"
            )

        return True

    def generate_inverse_recipe(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        preimage_hash: Optional[str],
        exists_before: bool,
    ) -> Optional[InverseOperationReference]:
        """Synthesize exact inverse recipe for filesystem operations."""
        if tool_name == "fs.create_file":
            # Inverse of create_file is delete_file
            return InverseOperationReference(
                inverse_tool_name="fs.delete_file",
                arguments={"path": arguments["path"]},
            )
        elif tool_name == "fs.write_file":
            if not exists_before:
                return InverseOperationReference(
                    inverse_tool_name="fs.delete_file",
                    arguments={"path": arguments["path"]},
                )
            else:
                return InverseOperationReference(
                    inverse_tool_name="fs.restore_preimage",
                    arguments={"path": arguments["path"], "preimage_hash": preimage_hash},
                )
        elif tool_name == "fs.delete_file":
            return InverseOperationReference(
                inverse_tool_name="fs.restore_preimage",
                arguments={"path": arguments["path"], "preimage_hash": preimage_hash},
            )
        elif tool_name == "fs.move_file":
            return InverseOperationReference(
                inverse_tool_name="fs.move_file",
                arguments={
                    "source_path": arguments["destination_path"],
                    "destination_path": arguments["source_path"],
                },
            )
        return None
