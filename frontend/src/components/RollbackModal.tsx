import React, { useState } from 'react';
import { triggerRollback, RollbackSummary } from '../lib/api';

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

  const handleConfirm = async () => {
    setIsExecuting(true);
    try {
      const summary = await triggerRollback(sessionId, targetStepIndex, workspaceRoot);
      onComplete(summary);
    } catch (err) {
      console.error('Rollback failed:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.8)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="card" style={{ width: '500px', background: 'var(--bg-card)' }}>
        <h3 style={{ color: 'var(--accent-red)', marginBottom: '12px' }}>
          ⏪ Confirm REWIND Rollback
        </h3>
        <p style={{ marginBottom: '16px', lineHeight: '1.5' }}>
          You are about to rewind workspace state back to <strong>Step #{targetStepIndex}</strong>.
          All actions executed after Step #{targetStepIndex} will be deterministically reversed using pre-image inverse recipes.
        </p>

        <div className="diff-box" style={{ marginBottom: '20px' }}>
          <div>Target Session: {sessionId.slice(0, 8)}...</div>
          <div>Target Step: #{targetStepIndex}</div>
          <div>Strategy: REVERSE_TOPOLOGICAL_INVERSE_DAG</div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button className="btn" onClick={onClose} disabled={isExecuting} style={{ background: 'var(--border-color)', color: '#fff' }}>
            Cancel
          </button>
          <button className="btn btn-danger" onClick={handleConfirm} disabled={isExecuting}>
            {isExecuting ? 'Rolling Back...' : 'Execute REWIND'}
          </button>
        </div>
      </div>
    </div>
  );
};
