export interface Session {
  session_id: string;
  workspace_root: string;
  goal_prompt: string;
  status: string;
  created_at: string;
}

export interface ActionItem {
  action_id: string;
  session_id: string;
  step_index: number;
  tool_name: string;
  arguments: Record<string, any>;
  reasoning: string;
  status: string;
  risk_assessment: {
    score: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
    rationale: string;
    requires_approval: boolean;
  };
  reversibility_class: string;
  checkpoint_id?: string;
}

export interface CheckpointItem {
  checkpoint_id: string;
  session_id: string;
  step_index: number;
  git_state_ref: string;
  filesystem_state_ref: string;
  integrity_hash: string;
}

export interface RollbackSummary {
  rollback_id: string;
  rollback_plan_id: string;
  session_id: string;
  target_step_index: number;
  status: string;
  reverted_action_ids: string[];
  failed_action_id?: string;
  error_message?: string;
}

export interface DemoExecutionSummary {
  session_id: string;
  workspace_root: string;
  total_steps_executed: number;
  rollback_summary: RollbackSummary;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function createSession(workspace_root: string, goal_prompt: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workspace_root, goal_prompt }),
  });
  return res.json();
}

export async function listActions(session_id: string): Promise<ActionItem[]> {
  const res = await fetch(`${API_BASE}/sessions/${session_id}/actions`);
  return res.json();
}

export async function listCheckpoints(session_id: string): Promise<CheckpointItem[]> {
  const res = await fetch(`${API_BASE}/sessions/${session_id}/checkpoints`);
  return res.json();
}

export async function triggerRollback(
  session_id: string,
  target_step_index: number,
  workspace_root: string
): Promise<RollbackSummary> {
  const res = await fetch(`${API_BASE}/rollbacks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id, target_step_index, workspace_root }),
  });
  return res.json();
}

export async function runDemoScenario(workspace_root: string): Promise<DemoExecutionSummary> {
  const res = await fetch(`${API_BASE}/demo/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workspace_root }),
  });
  return res.json();
}

export async function approveAction(action_id: string): Promise<ActionItem> {
  const res = await fetch(`${API_BASE}/actions/${action_id}/approve`, { method: 'POST' });
  return res.json();
}

export async function rejectAction(action_id: string): Promise<ActionItem> {
  const res = await fetch(`${API_BASE}/actions/${action_id}/reject`, { method: 'POST' });
  return res.json();
}
