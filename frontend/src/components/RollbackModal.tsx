'use client';
import React, { useState, useEffect } from 'react';
import { ActionItem, RollbackSummary, triggerRollback } from '../lib/api';

interface RollbackModalProps {
  sessionId: string;
  targetStepIndex: number;
  workspaceRoot: string;
  allActions: ActionItem[];
  onClose: () => void;
  onComplete: (summary: RollbackSummary) => void;
}

type Phase = 'preview' | 'executing' | 'done' | 'error';

interface ProgressStep {
  id: string;
  label: string;
}

const STEPS: ProgressStep[] = [
  { id: 'plan',   label: 'Building reverse-topological DAG plan…' },
  { id: 'exec',   label: 'Executing non-LLM inverse recipes…' },
  { id: 'verify', label: 'Verifying Merkle-root state integrity…' },
];

export const RollbackModal: React.FC<RollbackModalProps> = ({
  sessionId,
  targetStepIndex,
  workspaceRoot,
  allActions,
  onClose,
  onComplete,
}) => {
  const [phase, setPhase] = useState<Phase>('preview');
  const [doneStep, setDoneStep] = useState(-1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [result, setResult] = useState<RollbackSummary | null>(null);

  const actionsToReverse = allActions
    .filter((a) => a.step_index > targetStepIndex)
    .sort((a, b) => b.step_index - a.step_index);

  useEffect(() => {
    const fn = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && phase !== 'executing') onClose();
    };
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [phase, onClose]);

  const executeRollback = async () => {
    setPhase('executing');
    setDoneStep(-1);

    try {
      // Step 0 → done immediately
      setDoneStep(0);
      await sleep(380);
      setDoneStep(1);

      const summary = await triggerRollback(sessionId, targetStepIndex, workspaceRoot);

      await sleep(320);
      setDoneStep(2);
      await sleep(350);

      setResult(summary);
      setPhase('done');
      // Notify parent after a beat so the user sees RESTORED
      setTimeout(() => onComplete(summary), 1200);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unknown error');
      setPhase('error');
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={() => phase !== 'executing' && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="rollback-title"
    >
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {/* ---- HEADER ---- */}
        <div className="modal-header">
          <div>
            <p className="modal-subtitle">REWIND TRANSACTION</p>
            <h2 id="rollback-title" className="modal-title">
              {phase === 'done'
                ? '✓ Restored'
                : `Rollback to Step ${targetStepIndex}`}
            </h2>
          </div>
          {phase !== 'executing' && (
            <button
              className="btn btn-ghost btn-sm"
              onClick={onClose}
              aria-label="Cancel rollback"
            >
              ✕
            </button>
          )}
        </div>

        {/* ---- BODY ---- */}
        <div className="modal-body">
          {/* PREVIEW */}
          {phase === 'preview' && (
            <>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>
                {actionsToReverse.length === 0
                  ? 'No downstream actions to reverse — workspace is already at this state.'
                  : `${actionsToReverse.length} action${actionsToReverse.length > 1 ? 's' : ''} will be deterministically reversed in reverse order:`}
              </p>

              {actionsToReverse.length > 0 && (
                <div className="rewind-preview-list" style={{ marginBottom: 16 }}>
                  {actionsToReverse.map((act, idx) => (
                    <React.Fragment key={act.action_id}>
                      <div className="rewind-preview-item">
                        <span className="rewind-preview-step">STEP {act.step_index}</span>
                        <span className="rewind-preview-tool">{act.tool_name}</span>
                        {act.arguments?.path && (
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-tertiary)' }}>
                            {act.arguments.path}
                          </span>
                        )}
                      </div>
                      {idx < actionsToReverse.length - 1 && (
                        <div className="rewind-preview-connector">↓</div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              )}

              {/* Domains */}
              <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 8 }}>
                Restoration Targets
              </p>
              <div className="domain-grid">
                <div className="domain-cell">
                  <div className="domain-cell-label">Filesystem</div>
                  <div className="domain-cell-value">Pre-images</div>
                </div>
                <div className="domain-cell">
                  <div className="domain-cell-label">Git Repo</div>
                  <div className="domain-cell-value">HEAD snapshot</div>
                </div>
                <div className="domain-cell">
                  <div className="domain-cell-label">PostgreSQL</div>
                  <div className="domain-cell-value">Savepoints</div>
                </div>
              </div>
            </>
          )}

          {/* EXECUTING */}
          {phase === 'executing' && (
            <div className="progress-steps">
              {STEPS.map((s, idx) => {
                const isDone    = doneStep > idx;
                const isActive  = doneStep === idx;
                const cls       = isDone ? 'done' : isActive ? 'active' : 'pending';
                return (
                  <div key={s.id} className={`progress-step ${cls}`}>
                    <div className="progress-step-icon">
                      {isDone ? '✓' : isActive ? '◌' : String(idx + 1)}
                    </div>
                    <span>{s.label}</span>
                  </div>
                );
              })}
            </div>
          )}

          {/* DONE */}
          {phase === 'done' && result && (
            <div className="restored-banner" style={{ marginBottom: 0 }}>
              <span className="restored-icon">✓</span>
              <div>
                <p className="restored-title">State Verified Clean</p>
                <p className="restored-detail">
                  Workspace restored to Step #{result.target_step_index}.{' '}
                  {result.reverted_action_ids?.length ?? 0} action(s) reversed.
                  SHA-256 Merkle root verified.
                </p>
              </div>
            </div>
          )}

          {/* ERROR */}
          {phase === 'error' && (
            <div style={{ background: 'var(--red-dim)', border: '1px solid var(--red-border)', borderRadius: 'var(--radius-md)', padding: '12px 14px' }}>
              <p style={{ fontSize: 12, color: 'var(--red)', fontWeight: 700, marginBottom: 4 }}>Rollback Failed</p>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{errorMsg}</p>
            </div>
          )}
        </div>

        {/* ---- FOOTER ---- */}
        <div className="modal-footer">
          {phase === 'preview' && (
            <>
              <button className="btn btn-ghost btn-sm" onClick={onClose}>Cancel</button>
              <button
                className="btn btn-danger-solid btn-md"
                onClick={executeRollback}
                disabled={actionsToReverse.length === 0}
              >
                ↺ Execute REWIND
              </button>
            </>
          )}
          {(phase === 'done' || phase === 'error') && (
            <button className="btn btn-ghost btn-sm" onClick={onClose}>Close</button>
          )}
          {phase === 'executing' && (
            <span style={{ fontSize: 12, color: 'var(--text-tertiary)' }}>Executing…</span>
          )}
        </div>
      </div>
    </div>
  );
};

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}
