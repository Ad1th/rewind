"""FastAPI REST Control Plane Router."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from backend.api.service import ControlPlaneRuntimeCoordinator
from backend.db.repositories import (
    PersistenceRepository,
    RollbackRecordEntity,
    SessionEntity,
    WorkspaceEntity,
)
from agent.demo.canonical_demo import CanonicalDemoRunner, DemoExecutionSummary
from agent.runtime.approval import ApprovalManager
from agent.runtime.checkpoint import CheckpointRecord
from agent.runtime.contracts import Action


router = APIRouter(prefix="/api/v1", tags=["Control Plane API"])

# Dependency Injection Singleton Coordinator instance
_coordinator_instance = ControlPlaneRuntimeCoordinator()
_approval_mgr = ApprovalManager(_coordinator_instance.repo, _coordinator_instance.event_bus)

def get_coordinator() -> ControlPlaneRuntimeCoordinator:
    return _coordinator_instance

def get_repository() -> PersistenceRepository:
    return _coordinator_instance.repo

def get_approval_manager() -> ApprovalManager:
    return _approval_mgr


# --- Request & Response Models ---

class CreateWorkspaceRequest(BaseModel):
    workspace_root: str
    name: str = "default_workspace"

    model_config = ConfigDict(frozen=True)


class CreateSessionRequest(BaseModel):
    workspace_root: str
    goal_prompt: str

    model_config = ConfigDict(frozen=True)


class RunDemoRequest(BaseModel):
    workspace_root: str = "/tmp/rewind_demo_workspace"

    model_config = ConfigDict(frozen=True)


class TriggerRollbackRequest(BaseModel):
    session_id: str
    target_step_index: int
    workspace_root: str

    model_config = ConfigDict(frozen=True)


class ActionDiffResponse(BaseModel):
    action_id: str
    step_index: int
    tool_name: str
    pre_state_ref: Dict[str, Any]
    post_state_ref: Dict[str, Any]
    diff_lines: List[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


# --- Workspaces Endpoints ---

@router.post("/workspaces", status_code=status.HTTP_201_CREATED, response_model=WorkspaceEntity)
async def create_workspace(
    req: CreateWorkspaceRequest,
    repo: PersistenceRepository = Depends(get_repository),
):
    return await repo.create_workspace(req.workspace_root, req.name)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceEntity)
async def get_workspace(
    workspace_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    ws = await repo.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")
    return ws


# --- Sessions Endpoints ---

@router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=SessionEntity)
async def create_session(
    req: CreateSessionRequest,
    repo: PersistenceRepository = Depends(get_repository),
):
    return await repo.create_session(req.workspace_root, req.goal_prompt)


@router.get("/sessions/{session_id}", response_model=SessionEntity)
async def get_session(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session


@router.post("/sessions/{session_id}/pause", response_model=SessionEntity)
async def pause_session(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return await repo.update_session_status(session_id, "PAUSED")


@router.post("/sessions/{session_id}/resume", response_model=SessionEntity)
async def resume_session(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return await repo.update_session_status(session_id, "RUNNING")


# --- Actions Endpoints ---

@router.get("/sessions/{session_id}/actions", response_model=List[Action])
async def list_session_actions(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    return await repo.list_actions(session_id)


@router.get("/actions/{action_id}", response_model=Action)
async def get_action(
    action_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    action = await repo.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found.")
    return action


@router.post("/actions/{action_id}/approve", response_model=Action)
async def approve_action(
    action_id: str,
    approval_mgr: ApprovalManager = Depends(get_approval_manager),
):
    try:
        return await approval_mgr.approve_action(action_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/actions/{action_id}/reject", response_model=Action)
async def reject_action(
    action_id: str,
    approval_mgr: ApprovalManager = Depends(get_approval_manager),
):
    try:
        return await approval_mgr.reject_action(action_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.get("/actions/{action_id}/diff", response_model=ActionDiffResponse)
async def get_action_diff(
    action_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    action = await repo.get_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found.")

    diff_lines = action.post_state_ref.get("diff_lines", ["- old_content", "+ new_content"])
    return ActionDiffResponse(
        action_id=action.action_id,
        step_index=action.step_index,
        tool_name=action.tool_name,
        pre_state_ref=action.pre_state_ref,
        post_state_ref=action.post_state_ref,
        diff_lines=diff_lines,
    )


# --- Checkpoints Endpoints ---

@router.get("/sessions/{session_id}/checkpoints", response_model=List[CheckpointRecord])
async def list_session_checkpoints(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    return await repo.list_checkpoints(session_id)


@router.get("/checkpoints/{checkpoint_id}", response_model=CheckpointRecord)
async def get_checkpoint(
    checkpoint_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    chk = await repo.get_checkpoint(checkpoint_id)
    if not chk:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found.")
    return chk


# --- Rollbacks Endpoints ---

@router.post("/rollbacks", response_model=RollbackRecordEntity)
async def trigger_rollback(
    req: TriggerRollbackRequest,
    coordinator: ControlPlaneRuntimeCoordinator = Depends(get_coordinator),
):
    return await coordinator.execute_rollback_from_api(
        session_id=req.session_id,
        target_step_index=req.target_step_index,
        workspace_root=req.workspace_root,
    )


@router.get("/sessions/{session_id}/rollbacks", response_model=List[RollbackRecordEntity])
async def list_session_rollbacks(
    session_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    return await repo.list_rollbacks(session_id)


@router.get("/rollbacks/{rollback_id}", response_model=RollbackRecordEntity)
async def get_rollback(
    rollback_id: str,
    repo: PersistenceRepository = Depends(get_repository),
):
    rb = await repo.get_rollback(rollback_id)
    if not rb:
        raise HTTPException(status_code=404, detail=f"Rollback '{rollback_id}' not found.")
    return rb


# --- Demo Endpoints ---

@router.post("/demo/run", response_model=DemoExecutionSummary)
async def run_demo_scenario(
    req: RunDemoRequest,
    repo: PersistenceRepository = Depends(get_repository),
):
    runner = CanonicalDemoRunner(req.workspace_root)
    summary = await runner.run_canonical_demo("sess-canonical-demo")
    
    # Register session in repo
    await repo.create_session(req.workspace_root, "Canonical Hackathon Demo Task")
    for act in runner.dag_manager._nodes.values():
        await repo.save_action(act.action)

    return summary
