import React from 'react';
import { ActionItem } from '../lib/api';

interface ActionTimelineProps {
  actions: ActionItem[];
  onInspect: (action: ActionItem) => void;
  onRollback: (stepIndex: number) => void;
  onRunDemo?: () => void;
}

export const ActionTimeline: React.FC<ActionTimelineProps> = ({
  actions,
  onInspect,
  onRollback,
  onRunDemo,
}) => {
  if (!actions || actions.length === 0) {
    return (
      <div
        className="card-panel"
        style={{
          textAlign: 'center',
          padding: '48px 24px',
          borderStyle: 'dashed',
          borderColor: 'var(--border-color)',
        }}
      >
        <div
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: 'rgba(0, 240, 255, 0.08)',
            color: 'var(--accent-cyan)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            fontSize: '1.2rem',
            fontWeight: 700,
          }}
        >
          ⏱️
        </div>
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>
          NO ACTIONS RECORDED YET
        </h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 20px' }}>
          Run the interactive demo to watch an agent plan, execute, checkpoint, and rewind state in real time.
        </p>
        {onRunDemo && (
          <button className="btn-action btn-hero" onClick={onRunDemo}>
            ⚡ Run Interactive Demo
          </button>
        )}
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', paddingLeft: '24px' }}>
      {/* Vertical Connecting Line */}
      <div
        style={{
          position: 'absolute',
          left: '11px',
          top: '20px',
          bottom: '20px',
          width: '2px',
          background: 'linear-gradient(180deg, var(--accent-cyan) 0%, var(--border-color) 100%)',
          zIndex: 1,
        }}
      />

      {actions.map((act, index) => {
        const isCheckpoint = act.checkpoint_id || act.step_index === 1 || act.step_index === 2;
        const riskScore = act.risk_assessment?.score || 'LOW';
        
        let riskBadgeClass = 'badge-low';
        if (riskScore === 'MEDIUM') riskBadgeClass = 'badge-medium';
        if (riskScore === 'HIGH' || riskScore === 'CRITICAL') riskBadgeClass = 'badge-high';

        return (
          <div
            key={act.action_id || index}
            style={{
              position: 'relative',
              marginBottom: '24px',
              zIndex: 2,
            }}
          >
            {/* Timeline Node Bullet */}
            <div
              style={{
                position: 'absolute',
                left: '-24px',
                top: '22px',
                transform: 'translateX(-50%)',
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                background: isCheckpoint ? 'var(--accent-cyan)' : 'var(--bg-card)',
                border: `3px solid ${isCheckpoint ? 'var(--bg-dark)' : 'var(--border-active)'}`,
                boxShadow: isCheckpoint ? '0 0 10px var(--accent-cyan)' : 'none',
              }}
            />

            {/* Action Card Surface */}
            <div className="card-panel" style={{ margin: 0, background: 'var(--bg-card)' }}>
              {/* Header Bar */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    className="font-mono"
                    style={{
                      fontSize: '0.8rem',
                      fontWeight: 800,
                      color: 'var(--text-dim)',
                      background: '#1e293b',
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}
                  >
                    STEP #{act.step_index}
                  </span>
                  {isCheckpoint && (
                    <span
                      style={{
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: 'var(--accent-cyan)',
                        letterSpacing: '0.05em',
                      }}
                    >
                      ● CHECKPOINT
                    </span>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge-tag ${riskBadgeClass}`}>
                    {riskScore} RISK
                  </span>
                  <span className="badge-tag badge-reversible">
                    ↶ Fully reversible
                  </span>
                </div>
              </div>

              {/* Tool Name & Resource Target */}
              <div style={{ marginBottom: '10px' }}>
                <div className="font-mono" style={{ fontSize: '1rem', fontWeight: 700, color: '#fff' }}>
                  {act.tool_name}
                </div>
                <div className="font-mono" style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  {act.arguments?.path || act.arguments?.target_path || act.arguments?.table_name || 'workspace'}
                </div>
              </div>

              {/* Reasoning Description */}
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: 1.4 }}>
                {act.reasoning}
              </p>

              {/* Card Footer Actions */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  paddingTop: '12px',
                  borderTop: '1px solid rgba(255, 255, 255, 0.06)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--accent-green)' }}>
                  <span>✓ COMMITTED</span>
                </div>

                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    className="btn-action btn-secondary"
                    onClick={() => onInspect(act)}
                    aria-label={`Inspect diff for step ${act.step_index}`}
                  >
                    Inspect Diff
                  </button>
                  <button
                    className="btn-action btn-rewind"
                    onClick={() => onRollback(act.step_index)}
                    aria-label={`Rewind to step ${act.step_index}`}
                  >
                    Rewind to here
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
