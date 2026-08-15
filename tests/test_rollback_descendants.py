import os
import pytest

from backend.api.service import ControlPlaneRuntimeCoordinator
from agent.demo.canonical_demo import CanonicalDemoRunner


@pytest.mark.asyncio
async def test_rollback_descendants_count_accuracy(tmp_path):
    workspace = tmp_path / "descendants_test_workspace"
    ws_root = str(workspace)

    coordinator = ControlPlaneRuntimeCoordinator()
    runner = CanonicalDemoRunner(ws_root, coordinator=coordinator)

    # Execute 4 steps (Steps 1, 2, 3, 4) into shared coordinator DAG
    demo_summary = await runner.run_demo_steps("sess-descendant-test")
    assert demo_summary.total_steps_executed == 4

    # Trigger rollback to Step #1 (reverting steps 4, 3, 2)
    rb_record = await coordinator.execute_rollback_from_api(
        session_id="sess-descendant-test",
        target_step_index=1,
        workspace_root=ws_root,
    )

    assert rb_record.status == "RESTORED"
    assert len(rb_record.reverted_action_ids) == 3

    # Assert workspace restored to step 1 state (main.py content = v1)
    main_file = workspace / "src" / "main.py"
    assert main_file.exists()
    assert main_file.read_text() == "print('v1 initial app')"

    # Assert config.json deleted
    config_file = workspace / "config.json"
    assert not config_file.exists()


@pytest.mark.asyncio
async def test_rollback_to_step2_descendants(tmp_path):
    workspace = tmp_path / "descendants_step2_workspace"
    ws_root = str(workspace)

    coordinator = ControlPlaneRuntimeCoordinator()
    runner = CanonicalDemoRunner(ws_root, coordinator=coordinator)

    await runner.run_demo_steps("sess-step2-test")

    # Trigger rollback to Step #2 (reverting steps 4, 3)
    rb_record = await coordinator.execute_rollback_from_api(
        session_id="sess-step2-test",
        target_step_index=2,
        workspace_root=ws_root,
    )

    assert rb_record.status == "RESTORED"
    assert len(rb_record.reverted_action_ids) == 2

    main_file = workspace / "src" / "main.py"
    assert main_file.exists()
    assert main_file.read_text() == "print('v2 feature added')"
