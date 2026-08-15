import os
import subprocess
import pytest

from agent.execution.git_worktree import GitWorktreeDriver, GitWorktreeDriverError


@pytest.fixture
def temp_git_repo(tmp_path) -> str:
    repo = tmp_path / "test_repo"
    repo.mkdir()
    repo_str = str(repo)

    # Init git repo safely
    subprocess.run(["git", "init"], cwd=repo_str, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(["git", "config", "user.name", "REWIND Test"], cwd=repo_str, check=True)
    subprocess.run(["git", "config", "user.email", "test@rewind.dev"], cwd=repo_str, check=True)

    # Create initial commit
    init_file = repo / "README.md"
    init_file.write_text("# Initial Repo")
    subprocess.run(["git", "add", "README.md"], cwd=repo_str, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_str, check=True)

    return repo_str


@pytest.fixture
def git_driver() -> GitWorktreeDriver:
    return GitWorktreeDriver()


def test_git_worktree_init_and_snapshot(temp_git_repo: str, git_driver: GitWorktreeDriver):
    session_id = "sess-test-12345"
    worktree_path = git_driver.init_worktree(temp_git_repo, session_id)

    assert os.path.exists(worktree_path)
    assert os.path.exists(os.path.join(worktree_path, "README.md"))

    # Initial commit snapshot
    init_commit = git_driver.capture_commit_snapshot(worktree_path, step_index=0)
    assert len(init_commit) == 40

    # Modify file and create step 1 snapshot
    file1 = os.path.join(worktree_path, "file1.txt")
    with open(file1, "w") as f:
        f.write("Step 1 content")

    step1_commit = git_driver.capture_commit_snapshot(worktree_path, step_index=1)
    assert step1_commit != init_commit

    # Restore step 0 commit snapshot
    restored = git_driver.restore_commit_snapshot(worktree_path, init_commit)
    assert restored is True
    assert not os.path.exists(file1)
    assert git_driver.verify_worktree_commit(worktree_path, init_commit)

    # Cleanup
    git_driver.cleanup_worktree(temp_git_repo, session_id)
    assert not os.path.exists(worktree_path)


def test_invalid_repo_raises_error(git_driver: GitWorktreeDriver, tmp_path):
    not_repo = tmp_path / "not_repo"
    not_repo.mkdir()

    with pytest.raises(GitWorktreeDriverError):
        git_driver.init_worktree(str(not_repo), "sess-999")
