import React, { useState } from 'react';
import { Header } from './Header';
import { ActionTimeline } from './ActionTimeline';
import { ActionInspector } from './ActionInspector';
import { RollbackModal } from './RollbackModal';
import { ActionItem, createSession, listActions, RollbackSummary } from '../lib/api';
import { useTelemetry } from '../lib/useTelemetry';

export const TimeMachineUI: React.FC = () => {
  const [workspaceRoot, setWorkspaceRoot] = useState('/tmp/rewind_workspace');
  const [goalPrompt, setGoalPrompt] = useState('Build Python web app and write configuration file');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [inspectedAction, setInspectedAction] = useState<ActionItem | null>(null);
  const [rollbackStep, setRollbackStep] = useState<number | null>(null);
  const [lastRollbackResult, setLastRollbackResult] = useState<RollbackSummary | null>(null);

  const { isConnected } = useTelemetry(sessionId);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const session = await createSession(workspaceRoot, goalPrompt);
      setSessionId(session.session_id);
      
      // Fetch initial actions
      const fetched = await listActions(session.session_id);
      setActions(fetched);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleRollbackComplete = (summary: RollbackSummary) => {
    setLastRollbackResult(summary);
    setRollbackStep(null);
    if (sessionId) {
      listActions(sessionId).then(setActions);
    }
  };

  return (
    <div>
      <Header sessionId={sessionId} isConnected={isConnected} />

      <div className="container">
        {/* Workspace & Task Prompt Form */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '12px' }}>Workspace Task Setup</h2>
          <form onSubmit={handleStartSession} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Workspace Path (Jailed Root)
              </label>
              <input
                type="text"
                value={workspaceRoot}
                onChange={(e) => setWorkspaceRoot(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-dark)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '6px' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Agent Goal Prompt
              </label>
              <input
                type="text"
                value={goalPrompt}
                onChange={(e) => setGoalPrompt(e.target.value)}
                style={{ width: '100%', padding: '8px 12px', background: 'var(--bg-dark)', border: '1px solid var(--border-color)', color: '#fff', borderRadius: '6px' }}
              />
            </div>
            <div>
              <button type="submit" className="btn btn-primary">
                🚀 Launch REWIND Agent Session
              </button>
            </div>
          </form>
        </div>

        {/* Rollback Result Banner */}
        {lastRollbackResult && (
          <div className="card" style={{ borderLeft: '4px solid var(--accent-cyan)' }}>
            <h4 style={{ color: 'var(--accent-cyan)' }}>⏪ Rollback Outcome: {lastRollbackResult.status}</h4>
            <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>
              Restored workspace to Step #{lastRollbackResult.target_step_index}. Reverted {lastRollbackResult.reverted_action_ids.length} downstream actions.
            </p>
          </div>
        )}

        {/* Live Timeline */}
        <div style={{ marginTop: '32px' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Live Action Timeline</h3>
          <ActionTimeline
            actions={actions}
            onInspect={(act) => setInspectedAction(act)}
            onRollback={(stepIdx) => setRollbackStep(stepIdx)}
          />
        </div>
      </div>

      {/* Inspector Modal */}
      <ActionInspector action={inspectedAction} onClose={() => setInspectedAction(null)} />

      {/* Rollback Modal */}
      {rollbackStep !== null && sessionId && (
        <RollbackModal
          sessionId={sessionId}
          targetStepIndex={rollbackStep}
          workspaceRoot={workspaceRoot}
          onClose={() => setRollbackStep(null)}
          onComplete={handleRollbackComplete}
        />
      )}
    </div>
  );
};
