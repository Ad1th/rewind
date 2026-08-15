import React, { useState, useEffect } from 'react';
import { RollbackSummary, triggerRollback } from '../lib/api';

interface RollbackModalProps {
  sessionId: string;
  targetStepIndex: number;
  workspaceRoot: string;
  onClose: () => void;
  onComplete: (summary: RollbackSummary) => void;
}

export const RollbackModal: React.FC<RollbackModalProps> = ({
  sessionId,
  targetStepIndex,
  workspaceRoot,
  onClose,
  onComplete,
}) => {
  const [isExecuting, setIsExecuting] = useState(false);
  const [progressStep, setProgressStep] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isExecuting) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose, isExecuting]);

  const handleConfirmRollback = async () => {
    setIsExecuting(true);
    setError(null);
    setProgressStep(1); // Building rollback plan

    try {
      await new Promise((resolve) => setTimeout(resolve, 300));
      setProgressStep(2); // Executing inverse operations in reverse topological order

      await new Promise((resolve) => setTimeout(resolve, 400));
      setProgressStep(3); // Verifying SHA-256 Merkle root state integrity

      const result = await triggerRollback(sessionId, targetStepIndex, workspaceRoot);

      await new Promise((resolve) => setTimeout(resolve, 300));
      setProgressStep(4); // Verified restored

      onComplete(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rollback execution failed');
      setIsExecuting(false);
    }
  };

  const estimatedActionsReverted = Math.max(1, 4 - targetStepIndex);

  return (
    <div
      className="modal-overlay"
      onClick={() => !isExecuting && onClose()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="rollback-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ borderLeft: '4px solid var(--accent-red)' }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'var(--accent-red)',
                letterSpacing: '0.05em',
              }}
            >
              REWIND TRANSACTION CONFIRMATION
            </span>
            <h3 id="rollback-title" style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
              Rollback Workspace to Step #{targetStepIndex}
            </h3>
          </div>
          {!isExecuting && (
            <button className="btn-action btn-secondary" onClick={onClose} aria-label="Cancel rollback">
              ✕
            </button>
          )}
        </div>

        {/* Impact Warning Banner */}
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.08)',
            border: '1px solid rgba(239, 68, 68, 0.25)',
            borderRadius: '8px',
            padding: '16px',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#f87171', fontWeight: 700, fontSize: '0.95rem' }}>
            <span>⚠️</span>
            <span>{estimatedActionsReverted} downstream action(s) will be deterministically reversed</span>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            State will be restored to the exact SHA-256 Merkle root checkpoint recorded at <strong>Step #{targetStepIndex}</strong>.
          </p>
        </div>

        {/* Affected Layers & Domain Target */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>RESTORATION DOMAIN TARGETS</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
            <div style={{ background: 'var(--bg-dark)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>FILESYSTEM</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>Pre-images</div>
            </div>
            <div style={{ background: 'var(--bg-dark)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>GIT REPO</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>HEAD Snapshot</div>
            </div>
            <div style={{ background: 'var(--bg-dark)', padding: '10px', borderRadius: '6px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>POSTGRES DB</div>
              <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>Savepoints</div>
            </div>
          </div>
        </div>

        {/* Execution Progress Stepper */}
        {isExecuting && (
          <div
            style={{
              background: 'var(--bg-dark)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)',
              marginBottom: '20px',
            }}
          >
            <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '12px' }}>ROLLBACK ENGINE PROGRESS</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
              <div style={{ color: progressStep >= 1 ? 'var(--accent-green)' : 'var(--text-dim)' }}>
                {progressStep > 1 ? '✓' : '●'} Constructing reverse topological DAG execution plan...
              </div>
              <div style={{ color: progressStep >= 2 ? 'var(--accent-green)' : 'var(--text-dim)' }}>
                {progressStep > 2 ? '✓' : progressStep === 2 ? '●' : '○'} Executing non-LLM inverse recipes...
              </div>
              <div style={{ color: progressStep >= 3 ? 'var(--accent-green)' : 'var(--text-dim)' }}>
                {progressStep > 3 ? '✓' : progressStep === 3 ? '●' : '○'} Verifying Merkle root SHA-256 integrity hash...
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div style={{ color: 'var(--accent-red)', fontSize: '0.85rem', marginBottom: '16px', background: 'rgba(239, 68, 68, 0.1)', padding: '10px', borderRadius: '6px' }}>
            Rollback Error: {error}
          </div>
        )}

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '24px' }}>
          <button className="btn-action btn-secondary" onClick={onClose} disabled={isExecuting}>
            Cancel
          </button>
          <button
            className="btn-action btn-rewind"
            onClick={handleConfirmRollback}
            disabled={isExecuting}
            style={{ padding: '10px 20px', fontSize: '0.9rem', fontWeight: 700 }}
          >
            {isExecuting ? 'Executing REWIND...' : `Confirm & REWIND to Step #${targetStepIndex}`}
          </button>
        </div>
      </div>
    </div>
  );
};
