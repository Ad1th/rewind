'use client';
import React, { useEffect } from 'react';
import { ActionItem } from '../lib/api';

interface ActionInspectorProps {
  action: ActionItem | null;
  onClose: () => void;
}

function riskClass(score?: string) {
  switch (score) {
    case 'CRITICAL': return 'risk-critical';
    case 'HIGH':     return 'risk-high';
    case 'MEDIUM':   return 'risk-medium';
    default:         return 'risk-low';
  }
}

export const ActionInspector: React.FC<ActionInspectorProps> = ({ action, onClose }) => {
  useEffect(() => {
    if (!action) return;
    const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [action, onClose]);

  if (!action) return null;

  const path     = action.arguments?.path ?? action.arguments?.target_path ?? 'workspace';
  const content  = action.arguments?.content ?? null;
  const isCreate = action.tool_name?.includes('create');
  const isWrite  = action.tool_name?.includes('write');
  const isDelete = action.tool_name?.includes('delete');

  const beforeContent = isCreate
    ? '(file did not exist)'
    : isDelete
      ? content ?? '(file contents before deletion)'
      : '(previous file contents)';

  const afterContent = isDelete
    ? '(file deleted)'
    : content ?? '(new file contents)';

  return (
    <div
      className="modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="inspector-title"
    >
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <p className="modal-subtitle mono">STEP {String(action.step_index).padStart(2, '0')} — {action.tool_name}</p>
            <h2 id="inspector-title" className="modal-title">Action Inspector</h2>
          </div>
          <button
            className="btn btn-ghost btn-sm"
            onClick={onClose}
            aria-label="Close inspector"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Meta table */}
          <div className="meta-table">
            <div className="meta-cell">
              <div className="meta-cell-label">Risk</div>
              <div className="meta-cell-value">
                <span className={`risk-badge ${riskClass(action.risk_assessment?.score)}`}>
                  {action.risk_assessment?.score ?? 'LOW'}
                </span>
              </div>
            </div>
            <div className="meta-cell">
              <div className="meta-cell-label">Reversibility</div>
              <div className="meta-cell-value" style={{ color: 'var(--cyan)', fontSize: 12 }}>
                {action.reversibility_class?.replace(/_/g, ' ') ?? 'FULLY REVERSIBLE'}
              </div>
            </div>
            <div className="meta-cell">
              <div className="meta-cell-label">Resource</div>
              <div className="meta-cell-value" style={{ fontSize: 12, wordBreak: 'break-all' }}>{path}</div>
            </div>
          </div>

          {/* Rationale */}
          <div style={{ marginBottom: 16 }}>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 6 }}>
              Agent Reasoning
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>{action.reasoning}</p>
          </div>

          {action.risk_assessment?.rationale && (
            <div style={{ marginBottom: 16 }}>
              <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 6 }}>
                Risk Rationale
              </p>
              <p style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>{action.risk_assessment.rationale}</p>
            </div>
          )}

          {/* Diff */}
          <div>
            <p style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-tertiary)', marginBottom: 8 }}>
              State Diff
            </p>
            <div className="diff-grid">
              <div className="diff-panel">
                <div className="diff-panel-header before">
                  <span>−</span> BEFORE
                </div>
                <pre className="diff-content" style={{ color: 'var(--red)' }}>
                  {beforeContent}
                </pre>
              </div>
              <div className="diff-panel">
                <div className="diff-panel-header after">
                  <span>+</span> AFTER
                </div>
                <pre className="diff-content" style={{ color: 'var(--green)' }}>
                  {afterContent}
                </pre>
              </div>
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-ghost btn-sm" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};
