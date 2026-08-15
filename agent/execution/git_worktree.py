"""Git Worktree Execution, Snapshotting & Restoration Driver."""

import os
import subprocess
import shutil
from typing import List, Optional, Tuple

from agent.runtime.checkpoint import GitSnapshotProvider


class GitWorktreeDriverError(Exception):
    """Base exception for Git Worktree Driver operations."""
    pass


class GitWorktreeDriver(GitSnapshotProvider):
    """Executes zero-copy Git worktree snapshotting, commit tagging, and hard restorations."""

    def __init__(self, base_worktree_dir: Optional[str] = None) -> None:
        self.base_worktree_dir = base_worktree_dir

    def _run_git(self, cmd_args: List[str], cwd: str) -> Tuple[int, str, str]:
        """Execute a git command using safe list arguments (NO shell=True).
        
        Args:
            cmd_args: List of command arguments, e.g. ["git", "status", "--porcelain"]
            cwd: Working directory context.
            
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        full_cmd = ["git"] + cmd_args
        process = subprocess.run(
            full_cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return process.returncode, process.stdout.strip(), process.stderr.strip()

    def init_worktree(self, repo_path: str, session_id: str) -> str:
        """Create an isolated Git branch and worktree directory for the session.
        
        Branch format: rewind/session-<session_id>
        Worktree format: <repo_path>/.git/rewind-worktrees/session-<session_id>
        """
        if not os.path.exists(os.path.join(repo_path, ".git")):
            raise GitWorktreeDriverError(f"Target repository '{repo_path}' is not a valid Git repository.")

        branch_name = f"rewind/session-{session_id[:8]}"
        worktree_path = (
            os.path.join(self.base_worktree_dir, f"session-{session_id[:8]}")
            if self.base_worktree_dir
            else os.path.join(repo_path, ".git", "rewind-worktrees", f"session-{session_id[:8]}")
        )

        os.makedirs(os.path.dirname(worktree_path), exist_ok=True)

        # Create branch from HEAD if it doesn't exist
        code, out, err = self._run_git(["branch", branch_name, "HEAD"], cwd=repo_path)
        if code != 0 and "already exists" not in err:
            raise GitWorktreeDriverError(f"Failed to create branch '{branch_name}': {err}")

        # Add worktree
        code, out, err = self._run_git(["worktree", "add", "-f", worktree_path, branch_name], cwd=repo_path)
        if code != 0 and "already checked out" not in err:
            raise GitWorktreeDriverError(f"Failed to create worktree at '{worktree_path}': {err}")

        return worktree_path

    async def capture_snapshot(self, workspace_root: str, step_index: int) -> str:
        """Async GitSnapshotProvider implementation: capture current HEAD commit hash."""
        return self.capture_commit_snapshot(workspace_root, step_index)

    def capture_commit_snapshot(self, worktree_path: str, step_index: int) -> str:
        """Stage all workspace changes and create an automated snapshot commit."""
        # 1. Stage all changes
        code, _, err = self._run_git(["add", "-A"], cwd=worktree_path)
        if code != 0:
            raise GitWorktreeDriverError(f"git add -A failed: {err}")

        # 2. Check if there are changes to commit
        code, out, _ = self._run_git(["status", "--porcelain"], cwd=worktree_path)
        if not out:
            # No uncommitted changes, return current HEAD commit
            code, head_commit, err = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
            if code != 0:
                raise GitWorktreeDriverError(f"git rev-parse HEAD failed: {err}")
            return head_commit

        # 3. Create snapshot commit with --no-verify to bypass hooks
        commit_msg = f"rewind: checkpoint step {step_index}"
        code, _, err = self._run_git(["commit", "--no-verify", "-m", commit_msg], cwd=worktree_path)
        if code != 0:
            raise GitWorktreeDriverError(f"git commit failed: {err}")

        # 4. Get created commit hash
        code, commit_hash, err = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
        if code != 0:
            raise GitWorktreeDriverError(f"git rev-parse HEAD failed: {err}")

        return commit_hash

    def restore_commit_snapshot(self, worktree_path: str, commit_hash: str) -> bool:
        """Hard reset worktree state to target commit and clean untracked files."""
        # 1. Reset worktree --hard to target commit
        code, _, err = self._run_git(["reset", "--hard", commit_hash], cwd=worktree_path)
        if code != 0:
            raise GitWorktreeDriverError(f"git reset --hard '{commit_hash}' failed: {err}")

        # 2. Clean untracked files and directories
        code, _, err = self._run_git(["clean", "-fd"], cwd=worktree_path)
        if code != 0:
            raise GitWorktreeDriverError(f"git clean -fd failed: {err}")

        # 3. Verify HEAD commit matches target commit hash
        return self.verify_worktree_commit(worktree_path, commit_hash)

    def verify_worktree_commit(self, worktree_path: str, expected_commit_hash: str) -> bool:
        """Verify that worktree HEAD matches expected commit hash."""
        code, current_hash, err = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
        if code != 0:
            return False
        return current_hash.startswith(expected_commit_hash) or expected_commit_hash.startswith(current_hash)

    def cleanup_worktree(self, repo_path: str, session_id: str) -> bool:
        """Remove worktree path and delete session branch."""
        branch_name = f"rewind/session-{session_id[:8]}"
        worktree_path = (
            os.path.join(self.base_worktree_dir, f"session-{session_id[:8]}")
            if self.base_worktree_dir
            else os.path.join(repo_path, ".git", "rewind-worktrees", f"session-{session_id[:8]}")
        )

        if os.path.exists(worktree_path):
            self._run_git(["worktree", "remove", "-f", worktree_path], cwd=repo_path)
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)

        self._run_git(["branch", "-D", branch_name], cwd=repo_path)
        return True
