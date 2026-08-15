import React, { useEffect } from 'react';
import { ActionItem } from '../lib/api';

interface ActionInspectorProps {
  action: ActionItem | null;
  onClose: () => void;
}

export const ActionInspector: React.FC<ActionInspectorProps> = ({ action, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!action) return null;

  const content = action.arguments?.content || 'Sample restored state preimage content';
  const path = action.arguments?.path || 'workspace/resource';

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="inspector-title"
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <div className="font-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
              ACTION #{action.step_index}
            </div>
            <h3 id="inspector-title" className="font-mono" style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
              {action.tool_name}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="btn-action btn-secondary"
            aria-label="Close action inspector"
            style={{ padding: '6px 12px' }}
          >
            ✕
          </button>
        </div>

        {/* Metadata Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '12px',
            background: 'var(--bg-dark)',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid var(--border-color)',
            marginBottom: '20px',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>RISK LEVEL</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-amber)' }}>
              {action.risk_assessment?.score || 'LOW'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>REVERSIBILITY</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
              FULLY REVERSIBLE
            </div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>TARGET PATH</div>
            <div className="font-mono" style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              {path}
            </div>
          </div>
        </div>

        {/* Intent Reasoning */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '4px' }}>INTENT REASONING</div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', background: 'var(--bg-dark)', padding: '10px 14px', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            {action.reasoning}
          </p>
        </div>

        {/* Before / After State Diff Viewer */}
        <div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '8px' }}>STATE MUTATION DIFF</div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-red)', marginBottom: '4px', fontWeight: 700 }}>
                BEFORE
              </div>
              <pre
                className="font-mono"
                style={{
                  background: 'rgba(239, 68, 68, 0.05)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  color: '#f87171',
                  whiteSpace: 'pre-wrap',
                  minHeight: '80px',
                }}
              >
                {action.tool_name === 'fs.delete_file' ? `+ file exists: ${path}` : '- empty / preimage initial'}
              </pre>
            </div>

            <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', marginBottom: '4px', fontWeight: 700 }}>
                AFTER
              </div>
              <pre
                className="font-mono"
                style={{
                  background: 'rgba(16, 185, 129, 0.05)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '0.8rem',
                  color: '#34d399',
                  whiteSpace: 'pre-wrap',
                  minHeight: '80px',
                }}
              >
                {action.tool_name === 'fs.delete_file' ? `- file deleted: ${path}` : `+ ${content}`}
              </pre>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{ marginTop: '24px', textAlign: 'right' }}>
          <button className="btn-action btn-secondary" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
