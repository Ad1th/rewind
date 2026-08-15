import React from 'react';
import { ActionItem } from '../lib/api';

interface ActionTimelineProps {
  actions: ActionItem[];
  onInspect: (action: ActionItem) => void;
  onRollback: (stepIndex: number) => void;
}

export const ActionTimeline: React.FC<ActionTimelineProps> = ({
  actions,
  onInspect,
  onRollback,
}) => {
  if (actions.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
        No actions recorded in timeline yet. Submit a task prompt above to launch agent execution.
      </div>
    );
  }

  return (
    <div className="timeline">
      {actions.map((act) => (
        <div key={act.action_id} className="timeline-item">
          <div className="timeline-node">#{act.step_index}</div>
          <div className="timeline-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <code style={{ fontSize: '1rem', fontWeight: 600 }}>{act.tool_name}</code>
                <span className={`badge badge-${act.risk_assessment.score === 'LOW' ? 'green' : 'amber'}`}>
                  {act.risk_assessment.score} RISK
                </span>
                <span className="badge badge-cyan">{act.reversibility_class}</span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  className="btn"
                  onClick={() => onInspect(act)}
                  style={{ background: 'var(--border-color)', color: '#fff', padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Inspect Diff
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => onRollback(act.step_index)}
                  style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                >
                  Rewind to Step #{act.step_index}
                </button>
              </div>
            </div>

            <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginBottom: '8px' }}>
              {act.reasoning || 'Executed tool step.'}
            </p>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Path: {act.arguments.path || act.arguments.source_path || 'workspace'} | Status: {act.status}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
