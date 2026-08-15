import React from 'react';
import { ActionItem } from '../lib/api';

interface ActionInspectorProps {
  action: ActionItem | null;
  onClose: () => void;
}

export const ActionInspector: React.FC<ActionInspectorProps> = ({ action, onClose }) => {
  if (!action) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.75)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div className="card" style={{ width: '640px', maxWidth: '90vw', background: 'var(--bg-card)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.1rem' }}>Action Inspector — Step #{action.step_index}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <p><strong>Tool:</strong> <code>{action.tool_name}</code></p>
          <p><strong>Reasoning:</strong> {action.reasoning || 'N/A'}</p>
          <p><strong>Risk Score:</strong> <span className={`badge badge-${action.risk_assessment.score === 'LOW' ? 'green' : 'red'}`}>{action.risk_assessment.score}</span></p>
        </div>

        <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Raw Arguments</h4>
        <div className="diff-box" style={{ marginBottom: '16px' }}>
          <pre>{JSON.stringify(action.arguments, null, 2)}</pre>
        </div>

        <h4 style={{ marginBottom: '8px', fontSize: '0.9rem', color: 'var(--text-muted)' }}>State Transformation Diff</h4>
        <div className="diff-box">
          <div className="diff-del">- pre_state_ref: {action.tool_name} preimage</div>
          <div className="diff-add">+ post_state_ref: {action.tool_name} modified state</div>
        </div>

        <div style={{ marginTop: '20px', textAlign: 'right' }}>
          <button className="btn btn-primary" onClick={onClose}>Close Inspector</button>
        </div>
      </div>
    </div>
  );
};
