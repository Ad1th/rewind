import os
import pytest

from agent.execution.filesystem import FilesystemSandboxDriver, PreimageNotFoundError
from agent.security.jail import SecurityBoundaryViolation


@pytest.fixture
def workspace(tmp_path) -> str:
    ws = tmp_path / "workspace"
    ws.mkdir()
    return str(ws)


@pytest.fixture
def fs_driver() -> FilesystemSandboxDriver:
    return FilesystemSandboxDriver()


def test_create_file_and_inverse_restore(fs_driver: FilesystemSandboxDriver, workspace: str):
    rel_path = "src/main.py"
    
    # Capture preimage (file does not exist yet)
    preimage_hash, exists = fs_driver.capture_preimage(rel_path, workspace)
    assert preimage_hash is None
    assert exists is False

    # Execute create_file
    res = fs_driver.create_file(rel_path, "print('hello')", workspace)
    assert res.success is True
    assert os.path.exists(os.path.join(workspace, rel_path))

    # Generate inverse recipe
    recipe = fs_driver.generate_inverse_recipe("fs.create_file", {"path": rel_path}, preimage_hash, exists)
    assert recipe.inverse_tool_name == "fs.delete_file"

    # Execute inverse restoration
    restored = fs_driver.restore_preimage(rel_path, preimage_hash, workspace)
    assert restored is True
    assert not os.path.exists(os.path.join(workspace, rel_path))


def test_write_file_preimage_restoration(fs_driver: FilesystemSandboxDriver, workspace: str):
    rel_path = "config.json"
    full_path = os.path.join(workspace, rel_path)
    
    # Create initial file
    with open(full_path, "w") as f:
        f.write("original_content")

    # Capture preimage
    preimage_hash, exists = fs_driver.capture_preimage(rel_path, workspace)
    assert preimage_hash is not None
    assert exists is True

    # Overwrite file
    fs_driver.write_file(rel_path, "new_modified_content", workspace)
    with open(full_path) as f:
        assert f.read() == "new_modified_content"

    # Restore preimage
    fs_driver.restore_preimage(rel_path, preimage_hash, workspace)
    with open(full_path) as f:
        assert f.read() == "original_content"


def test_delete_file_preimage_restoration(fs_driver: FilesystemSandboxDriver, workspace: str):
    rel_path = "to_delete.txt"
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write("secret_data")

    preimage_hash, exists = fs_driver.capture_preimage(rel_path, workspace)
    fs_driver.delete_file(rel_path, workspace)
    assert not os.path.exists(full_path)

    # Restore deleted file
    fs_driver.restore_preimage(rel_path, preimage_hash, workspace)
    assert os.path.exists(full_path)
    with open(full_path) as f:
        assert f.read() == "secret_data"


def test_move_file(fs_driver: FilesystemSandboxDriver, workspace: str):
    src = "old_dir/file.txt"
    dest = "new_dir/file.txt"
    full_src = os.path.join(workspace, src)
    os.makedirs(os.path.dirname(full_src), exist_ok=True)
    with open(full_src, "w") as f:
        f.write("data")

    res = fs_driver.move_file(src, dest, workspace)
    assert res.success is True
    assert not os.path.exists(full_src)
    assert os.path.exists(os.path.join(workspace, dest))

    # Test inverse recipe generation
    recipe = fs_driver.generate_inverse_recipe("fs.move_file", {"source_path": src, "destination_path": dest}, None, True)
    assert recipe.inverse_tool_name == "fs.move_file"
    assert recipe.arguments["source_path"] == dest
    assert recipe.arguments["destination_path"] == src


def test_filesystem_driver_path_jail_enforcement(fs_driver: FilesystemSandboxDriver, workspace: str):
    with pytest.raises(SecurityBoundaryViolation):
        fs_driver.create_file("../../../etc/passwd", "data", workspace)

    with pytest.raises(SecurityBoundaryViolation):
        fs_driver.capture_preimage("../../outside.txt", workspace)
