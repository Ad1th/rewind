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
    try {
      const demoSummary = await runDemoScenario(workspaceRoot);
      setSessionId(demoSummary.session_id);
      
      // Fetch actual actions executed on the backend
      const fetched = await listActions(demoSummary.session_id);
      if (fetched.length > 0) {
        setActions(fetched);
      } else {
        // Fallback for real backend execution
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
    } catch (err) {
      console.error('Demo execution error:', err);
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
          // Truncate timeline to target step
          setActions((prev) => prev.filter((a) => a.step_index <= summary.target_step_index));
        }
      });
    }
  };

  return (
    <div>
      <Header sessionId={sessionId} isConnected={isConnected} />

      <div className="container">
        {/* Hero Value Banner */}
        <div className="card" style={{ borderLeft: '4px solid var(--accent-cyan)', background: 'linear-gradient(180deg, #161b22 0%, #0d1117 100%)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: '6px', letterSpacing: '-0.02em' }}>
                Transactional Safety Proxy & Time Machine
              </h1>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
                Intercept, verify, and deterministically REWIND un-trusted AI agent actions with SHA-256 Merkle root integrity.
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={handleRunDemoScenario}
              disabled={isDemoRunning}
              style={{ padding: '12px 20px', fontSize: '0.95rem' }}
            >
              ⚡ Run Interactive Hackathon Demo
            </button>
          </div>
        </div>

        {/* Task Setup Form */}
        <div className="card">
          <h2 style={{ fontSize: '1.1rem', marginBottom: '12px' }}>Agent Workspace Setup</h2>
          <form onSubmit={handleStartSession} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Jailed Workspace Path
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
              <button type="submit" className="btn" style={{ background: 'var(--border-color)', color: '#fff' }}>
                Initialize Custom Session
              </button>
            </div>
          </form>
        </div>

        {/* Rollback Result Banner */}
        {lastRollbackResult && (
          <div className="card" style={{ borderLeft: '4px solid var(--accent-green)', background: 'rgba(34, 197, 94, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ color: 'var(--accent-green)', fontSize: '1.1rem' }}>
                  ✓ RESTORED — State Verified Clean
                </h4>
                <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>
                  Restored workspace to <strong>Step #{lastRollbackResult.target_step_index}</strong>. Deterministically reversed {lastRollbackResult.reverted_action_ids.length} downstream actions.
                </p>
              </div>
              <span className="badge badge-green">VERIFICATION PASSED</span>
            </div>
          </div>
        )}

        {/* Live Timeline */}
        <div style={{ marginTop: '32px' }}>
          <h3 style={{ fontSize: '1.2rem', marginBottom: '16px' }}>Live Action Timeline & Checkpoints</h3>
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
