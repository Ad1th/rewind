import os
import pytest

from agent.demo.canonical_demo import CanonicalDemoRunner


@pytest.mark.asyncio
async def test_canonical_demo_execution(tmp_path):
    workspace = tmp_path / "demo_workspace"
    runner = CanonicalDemoRunner(str(workspace))

    summary = await runner.run_canonical_demo("sess-demo-test")

    assert summary.total_steps_executed == 4
    assert summary.rollback_summary is not None
    assert summary.rollback_summary.status == "RESTORED"
    assert summary.rollback_summary.target_step_index == 2
    assert len(summary.rollback_summary.reverted_action_ids) == 2

    # Assert restored file state: src/main.py restored to step 2 content
    main_file = workspace / "src" / "main.py"
    assert main_file.exists()
    assert main_file.read_text() == "print('v2 feature added')"

    # Assert config.json deleted by rollback
    config_file = workspace / "config.json"
    assert not config_file.exists()
