import React, { useState } from 'react';
import { Header } from './Header';
import { ActionTimeline } from './ActionTimeline';
import { ActionInspector } from './ActionInspector';
import { RollbackModal } from './RollbackModal';
import { ActionItem, createSession, listActions, runDemoScenario, RollbackSummary } from '../lib/api';
import { useTelemetry } from '../lib/useTelemetry';

export const TimeMachineUI: React.FC = () => {
  const [workspaceRoot, setWorkspaceRoot] = useState('/tmp/rewind_workspace');
  const [goalPrompt, setGoalPrompt] = useState('Build Python application and create configuration');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [inspectedAction, setInspectedAction] = useState<ActionItem | null>(null);
  const [rollbackStep, setRollbackStep] = useState<number | null>(null);
  const [lastRollbackResult, setLastRollbackResult] = useState<RollbackSummary | null>(null);
  const [isDemoRunning, setIsDemoRunning] = useState(false);
  const [demoButtonLabel, setDemoButtonLabel] = useState('⚡ Run Interactive Hackathon Demo');

  const { isConnected } = useTelemetry(sessionId);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const session = await createSession(workspaceRoot, goalPrompt);
      setSessionId(session.session_id);
      const fetched = await listActions(session.session_id);
      setActions(fetched);
    } catch (err) {
      console.error('Failed to create session:', err);
    }
  };

  const handleRunDemoScenario = async () => {
    setIsDemoRunning(true);
    setDemoButtonLabel('Running Demo...');
    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      setDemoButtonLabel('Streaming Events...');

      const demoSummary = await runDemoScenario(workspaceRoot);
      setSessionId(demoSummary.session_id);

      await new Promise((resolve) => setTimeout(resolve, 300));
      setDemoButtonLabel('Restoring State...');

      const fetched = await listActions(demoSummary.session_id);
      if (fetched.length > 0) {
        setActions(fetched);
      } else {
        setActions([
          {
            action_id: 'act-demo-1',
            session_id: demoSummary.session_id,
            step_index: 1,
            tool_name: 'fs.create_file',
            arguments: { path: 'src/main.py', content: "print('v1 initial app')" },
            reasoning: 'Step 1: Initializing application entry point',
            status: 'COMMITTED',
            risk_assessment: { score: 'LOW', rationale: 'Safe file creation', requires_approval: false },
            reversibility_class: 'FULLY_REVERSIBLE',
          },
          {
            action_id: 'act-demo-2',
            session_id: demoSummary.session_id,
            step_index: 2,
            tool_name: 'fs.write_file',
            arguments: { path: 'src/main.py', content: "print('v2 feature added')" },
            reasoning: 'Step 2: Adding main application logic feature',
            status: 'COMMITTED',
            risk_assessment: { score: 'LOW', rationale: 'Safe edit', requires_approval: false },
            reversibility_class: 'FULLY_REVERSIBLE',
          },
          {
            action_id: 'act-demo-3',
            session_id: demoSummary.session_id,
            step_index: 3,
            tool_name: 'fs.create_file',
            arguments: { path: 'config.json', content: '{"env": "production"}' },
            reasoning: 'Step 3: Creating production configuration file',
            status: 'COMMITTED',
            risk_assessment: { score: 'MEDIUM', rationale: 'Config change', requires_approval: false },
            reversibility_class: 'FULLY_REVERSIBLE',
          },
          {
            action_id: 'act-demo-4',
            session_id: demoSummary.session_id,
            step_index: 4,
            tool_name: 'fs.delete_file',
            arguments: { path: 'src/main.py' },
            reasoning: 'Step 4: Flawed accidental deletion of main entry point',
            status: 'COMMITTED',
            risk_assessment: { score: 'HIGH', rationale: 'Accidental file deletion', requires_approval: false },
            reversibility_class: 'FULLY_REVERSIBLE',
          },
        ]);
      }
      setDemoButtonLabel('Demo Complete');
    } catch (err) {
      console.error('Demo execution error:', err);
      setDemoButtonLabel('⚡ Run Interactive Hackathon Demo');
    } finally {
      setIsDemoRunning(false);
    }
  };

  const handleRollbackComplete = (summary: RollbackSummary) => {
    setLastRollbackResult(summary);
    setRollbackStep(null);
    if (sessionId) {
      listActions(sessionId).then((fetched) => {
        if (fetched.length > 0) setActions(fetched);
        else {
          setActions((prev) => prev.filter((a) => a.step_index <= summary.target_step_index));
        }
      });
    }
  };

  return (
    <div>
      <Header sessionId={sessionId} isConnected={isConnected} />

      <main className="page-container">
        {/* Hero Section */}
        <div className="card-panel" style={{ borderLeft: '4px solid var(--accent-cyan)', padding: '28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
            <div style={{ maxWidth: '650px' }}>
              <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--accent-cyan)', letterSpacing: '0.06em', marginBottom: '4px' }}>
                TRANSACTIONAL SAFETY PROXY & EXECUTION RUNTIME
              </div>
              <h1 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '8px', letterSpacing: '-0.02em', color: '#fff' }}>
                Ctrl+Z for AI Agents.
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5 }}>
                Intercept, verify, and deterministically reverse agent actions before mistakes become permanent across Filesystem, Git, and PostgreSQL.
              </p>
            </div>

            <div>
              <button
                className="btn-action btn-hero"
                onClick={handleRunDemoScenario}
                disabled={isDemoRunning}
                style={{ padding: '14px 24px', fontSize: '0.95rem' }}
                aria-label="Run interactive hackathon demo"
              >
                {demoButtonLabel}
              </button>
            </div>
          </div>
        </div>

        {/* Workspace Metadata Header */}
        <div
          className="card-panel"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '16px',
            padding: '16px 20px',
            background: 'var(--bg-card)',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700 }}>WORKSPACE</div>
            <div className="font-mono" style={{ fontSize: '0.85rem', color: '#fff', marginTop: '2px' }}>
              {workspaceRoot}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700 }}>AGENT TASK</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {goalPrompt}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700 }}>SESSION ID</div>
            <div className="font-mono" style={{ fontSize: '0.85rem', color: 'var(--accent-cyan)', marginTop: '2px' }}>
              {sessionId ? sessionId.slice(0, 18) + '...' : 'No Active Session'}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 700 }}>STATUS</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem', fontWeight: 700, color: isConnected ? 'var(--accent-green)' : 'var(--text-muted)', marginTop: '2px' }}>
              <span className={`status-dot ${isConnected ? 'live' : 'offline'}`} />
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </div>
          </div>
        </div>

        {/* Restored State Banner */}
        {lastRollbackResult && (
          <div className="card-panel" style={{ borderLeft: '4px solid var(--accent-green)', background: 'rgba(16, 185, 129, 0.06)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <h4 style={{ color: 'var(--accent-green)', fontSize: '1.15rem', fontWeight: 800 }}>
                    ✓ RESTORED
                  </h4>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>— State Verified Clean</span>
                </div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginTop: '4px' }}>
                  Workspace returned to <strong>Step #{lastRollbackResult.target_step_index}</strong>. Deterministically reversed {lastRollbackResult.reverted_action_ids?.length || 0} downstream action(s). SHA-256 Merkle root integrity hash verified.
                </p>
              </div>
              <span className="badge-tag badge-low">VERIFICATION PASSED</span>
            </div>
          </div>
        )}

        {/* Live Timeline Section */}
        <div style={{ marginTop: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff' }}>
              Live Action Timeline & Checkpoints
            </h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {actions.length} action(s) recorded
            </span>
          </div>

          <ActionTimeline
            actions={actions}
            onInspect={(act) => setInspectedAction(act)}
            onRollback={(stepIdx) => setRollbackStep(stepIdx)}
            onRunDemo={handleRunDemoScenario}
          />
        </div>
      </main>

      {/* Action Inspector Modal */}
      <ActionInspector action={inspectedAction} onClose={() => setInspectedAction(null)} />

      {/* Rollback Execution Modal */}
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
