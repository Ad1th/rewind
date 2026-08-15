"""Path Jailing and Workspace Boundary Verification."""

import os
from typing import List


class SecurityBoundaryViolation(Exception):
    """Raised when an operation attempts to escape the designated workspace jail."""
    pass


FORBIDDEN_SYSTEM_PATHS: List[str] = [
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/dev",
    "/proc",
    "/sys",
    "~/.ssh",
    "~/.aws",
]


def validate_jailed_path(target_path: str, workspace_root: str) -> str:
    """Validate that a target file/directory path lies strictly within the workspace root.
    
    Resolves relative segments (../), expands user shortcuts (~), and checks canonical
    symlink destinations to prevent workspace escaping attacks.
    
    Args:
        target_path: The proposed path string.
        workspace_root: Canonical root path of the managed workspace.
        
    Returns:
        The canonical, absolute path string if valid.
        
    Raises:
        SecurityBoundaryViolation: If path attempts traversal or escapes workspace root.
    """
    if not target_path or not target_path.strip():
        raise SecurityBoundaryViolation("Target path cannot be empty.")
        
    # Expand user paths (~/...)
    expanded_target = os.path.expanduser(target_path)
    canonical_workspace = os.path.realpath(os.path.expanduser(workspace_root))

    # Resolve absolute path for target
    if os.path.isabs(expanded_target):
        absolute_target = expanded_target
    else:
        absolute_target = os.path.join(canonical_workspace, expanded_target)

    # Canonicalize target path (resolves ../ and symlinks)
    canonical_target = os.path.realpath(absolute_target)

    # 1. Check path prefix containment
    if not (canonical_target == canonical_workspace or canonical_target.startswith(canonical_workspace + os.sep)):
        raise SecurityBoundaryViolation(
            f"Path traversal blocked: '{target_path}' resolves to '{canonical_target}', "
            f"which escapes workspace root '{canonical_workspace}'"
        )

    # 2. Check forbidden system path blocklist
    for forbidden in FORBIDDEN_SYSTEM_PATHS:
        canonical_forbidden = os.path.realpath(os.path.expanduser(forbidden))
        if (canonical_target == canonical_forbidden or canonical_target.startswith(canonical_forbidden + os.sep)) and not canonical_workspace.startswith(canonical_forbidden):
            raise SecurityBoundaryViolation(
                f"Access to forbidden system path blocked: '{target_path}' resolves to '{canonical_target}'"
            )

    return canonical_target
