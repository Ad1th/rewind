import pytest

from agent.execution.filesystem import FilesystemSandboxDriver
from agent.llm.provider import DeterministicDemoLLMProvider
from agent.rollback.dag import RollbackDAGManager
from agent.runtime.agent_loop import AgentLoop
from agent.runtime.checkpoint import CheckpointManager
from agent.runtime.contracts import ActionProposal, ActionStatus
from agent.runtime.event_bus import RuntimeEventBus
from agent.security.policy import PolicyEngine
from agent.security.risk import RiskEngine
from agent.tools.models import ReversibilityClass, RiskLevel, ToolDefinition
from agent.tools.registry import ToolRegistry


@pytest.fixture
def agent_components(tmp_path):
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="fs.create_file",
            description="Create file",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                "required": ["path", "content"],
            },
            permissions=["workspace.write"],
            risk_class=RiskLevel.LOW,
            reversibility_class=ReversibilityClass.FULLY_REVERSIBLE,
        )
    )

    policy_engine = PolicyEngine(registry)
    risk_engine = RiskEngine()
    checkpoint_mgr = CheckpointManager()
    dag_mgr = RollbackDAGManager()
    event_bus = RuntimeEventBus()

    proposal = ActionProposal(
        session_id="sess-agent-1",
        tool_name="fs.create_file",
        arguments={"path": "hello.py", "content": "print('world')"},
        reasoning="Creating hello script",
    )
    llm_provider = DeterministicDemoLLMProvider([proposal])

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()

    loop = AgentLoop(
        registry=registry,
        policy_engine=policy_engine,
        risk_engine=risk_engine,
        checkpoint_manager=checkpoint_mgr,
        dag_manager=dag_mgr,
        event_bus=event_bus,
        llm_provider=llm_provider,
    )

    return {"loop": loop, "workspace": str(workspace_dir)}


@pytest.mark.asyncio
async def test_agent_loop_executes_step(agent_components):
    loop: AgentLoop = agent_components["loop"]
    workspace: str = agent_components["workspace"]

    res = await loop.execute_step(
        session_id="sess-agent-1",
        goal_prompt="Build hello app",
        workspace_root=workspace,
    )

    assert res is not None
    assert res.accepted is True
    assert res.action is not None
    assert res.action.status == ActionStatus.COMMITTED
    assert res.result.success is True

    events = loop.event_bus.get_events("sess-agent-1")
    assert len(events) >= 1
