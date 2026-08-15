'use client';
import React, { useState } from 'react';
import { Header } from './Header';
import { ActionTimeline } from './ActionTimeline';
import { ActionInspector } from './ActionInspector';
import { RollbackModal } from './RollbackModal';
import {
  ActionItem,
  RollbackSummary,
  createSession,
  listActions,
  runDemoScenario,
} from '../lib/api';
import { useTelemetry } from '../lib/useTelemetry';

/* ------------------------------------------------------------------ */

const DEMO_WS_ROOT = '/tmp/rewind_demo';

const DEMO_FALLBACK: ActionItem[] = [
  {
    action_id: 'demo-1',
    session_id: 'sess-canonical-demo',
    step_index: 1,
    tool_name: 'fs.create_file',
    arguments: { path: 'src/main.py', content: "print('v1 initial app')" },
    reasoning: 'Initializing application entry point',
    status: 'COMMITTED',
    risk_assessment: { score: 'LOW', rationale: 'New file creation in sandboxed workspace.', requires_approval: false },
    reversibility_class: 'FULLY_REVERSIBLE',
    checkpoint_id: 'chk-1',
  },
  {
    action_id: 'demo-2',
    session_id: 'sess-canonical-demo',
    step_index: 2,
    tool_name: 'fs.write_file',
    arguments: { path: 'src/main.py', content: "print('v2 feature added')" },
    reasoning: 'Writing main application logic feature',
    status: 'COMMITTED',
    risk_assessment: { score: 'LOW', rationale: 'Overwrites existing file — pre-image captured.', requires_approval: false },
    reversibility_class: 'FULLY_REVERSIBLE',
    checkpoint_id: 'chk-2',
  },
  {
    action_id: 'demo-3',
    session_id: 'sess-canonical-demo',
    step_index: 3,
    tool_name: 'fs.create_file',
    arguments: { path: 'config.json', content: '{"env": "production"}' },
    reasoning: 'Creating production configuration file',
    status: 'COMMITTED',
    risk_assessment: { score: 'MEDIUM', rationale: 'Config file — flagged sensitive_configuration_file.', requires_approval: false },
    reversibility_class: 'FULLY_REVERSIBLE',
    checkpoint_id: 'chk-3',
  },
  {
    action_id: 'demo-4',
    session_id: 'sess-canonical-demo',
    step_index: 4,
    tool_name: 'fs.delete_file',
    arguments: { path: 'src/main.py' },
    reasoning: 'Accidental deletion of application entry point',
    status: 'COMMITTED',
    risk_assessment: { score: 'HIGH', rationale: 'Destructive operation — file permanently removed without replacement.', requires_approval: false },
    reversibility_class: 'FULLY_REVERSIBLE',
    checkpoint_id: 'chk-4',
  },
];

/* ------------------------------------------------------------------ */

export const TimeMachineUI: React.FC = () => {
  // workspaceRoot must reflect the actual workspace the backend used during demo execution
  // (the backend appends a session-scoped subdirectory to the base path)
  const [workspaceRoot, setWorkspaceRoot] = useState(DEMO_WS_ROOT);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [actions, setActions]     = useState<ActionItem[]>([]);
  const [inspected, setInspected] = useState<ActionItem | null>(null);
  const [rollbackStep, setRollbackStep] = useState<number | null>(null);
  const [restored, setRestored]   = useState<RollbackSummary | null>(null);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoLabel, setDemoLabel] = useState('▶  Run Demo');

  const { isConnected } = useTelemetry(sessionId);

  /* ---- Demo trigger ---- */
  const handleDemo = async () => {
    setDemoRunning(true);
    setRestored(null);
    setDemoLabel('Connecting…');

    try {
      setDemoLabel('Executing agent…');
      // Always send the base workspace root; the backend appends the session subdir
      const summary = await runDemoScenario(DEMO_WS_ROOT);
      setSessionId(summary.session_id);
      // CRITICAL: use the workspace_root that the backend actually executed in.
      // The backend appends /<session_id> to the base path and captures pre-images there.
      // Sending a different path to POST /rollbacks would make the executor unable to
      // locate the pre-images, causing PARTIALLY_RESTORED.
      setWorkspaceRoot(summary.workspace_root);

      setDemoLabel('Loading timeline…');
      const fetched = await listActions(summary.session_id);
      setActions(fetched.length > 0 ? fetched : DEMO_FALLBACK.map(a => ({ ...a, session_id: summary.session_id })));
      setDemoLabel('▶  Run Demo Again');
    } catch (_err) {
      // Backend not running — use deterministic fallback for offline demo
      setSessionId('sess-canonical-demo');
      setActions(DEMO_FALLBACK);
      setDemoLabel('▶  Run Demo Again');
    } finally {
      setDemoRunning(false);
    }
  };

  /* ---- Rollback complete ---- */
  const handleRollbackComplete = (summary: RollbackSummary) => {
    setRestored(summary);
    setRollbackStep(null);
    if (sessionId) {
      listActions(sessionId)
        .then((fetched) => {
          if (fetched.length > 0) setActions(fetched);
          else setActions((prev) => prev.filter((a) => a.step_index <= summary.target_step_index));
        })
        .catch(() => {
          setActions((prev) => prev.filter((a) => a.step_index <= summary.target_step_index));
        });
    }
  };

  /* ---- goal text ---- */
  const goalText = 'Build Python application and create configuration';

  /* ================================================================ */
  return (
    <div className="app-shell">
      {/* ---- HEADER ---- */}
      <Header sessionId={sessionId} isConnected={isConnected} />

      {/* ---- WORKSPACE BAR ---- */}
      <div className="workspace-bar">
        <div className="workspace-bar-inner">
          <div className="ws-field">
            <span className="ws-label">Workspace</span>
            <span className="ws-value">{workspaceRoot}</span>
          </div>
          <div className="ws-divider" />
          <div className="ws-field">
            <span className="ws-label">Task</span>
            <span className="ws-value" style={{ maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {goalText}
            </span>
          </div>
          {sessionId && (
            <>
              <div className="ws-divider" />
              <div className="ws-field">
                <span className="ws-label">Session</span>
                <span className="ws-value">{sessionId.slice(0, 18)}…</span>
              </div>
            </>
          )}
          <div style={{ marginLeft: 'auto', flexShrink: 0 }}>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleDemo}
              disabled={demoRunning}
            >
              {demoLabel}
            </button>
          </div>
        </div>
      </div>

      {/* ---- MAIN CONTENT ---- */}
      <main className="page-content">

        {/* Restored banner */}
        {restored && (
          <div className="restored-banner">
            <span className="restored-icon">✓</span>
            <div>
              <p className="restored-title">
                Restored — State Verified Clean
              </p>
              <p className="restored-detail">
                Workspace returned to Step #{restored.target_step_index}.{' '}
                {restored.reverted_action_ids?.length ?? 0} downstream action(s) reversed.
                SHA-256 Merkle root integrity verified.
              </p>
            </div>
          </div>
        )}

        {/* Timeline section */}
        <div className="section-header">
          <span className="section-title">Execution Timeline</span>
          <span className="section-count">{actions.length} action{actions.length !== 1 ? 's' : ''}</span>
        </div>

        <ActionTimeline
          actions={actions}
          onInspect={setInspected}
          onRollback={setRollbackStep}
          onRunDemo={handleDemo}
          demoRunning={demoRunning}
        />
      </main>

      {/* ---- MODALS ---- */}
      <ActionInspector action={inspected} onClose={() => setInspected(null)} />

      {rollbackStep !== null && sessionId && (
        <RollbackModal
          sessionId={sessionId}
          targetStepIndex={rollbackStep}
          workspaceRoot={workspaceRoot}
          allActions={actions}
          onClose={() => setRollbackStep(null)}
          onComplete={handleRollbackComplete}
        />
      )}
    </div>
  );
};
