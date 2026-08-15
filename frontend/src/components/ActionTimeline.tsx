'use client';
import React from 'react';
import { ActionItem } from '../lib/api';

/* ------------------------------------------------------------------ helpers */

function riskClass(score?: string) {
  switch (score) {
    case 'CRITICAL': return 'risk-critical';
    case 'HIGH':     return 'risk-high';
    case 'MEDIUM':   return 'risk-medium';
    default:         return 'risk-low';
  }
}

function revLabel(cls?: string) {
  if (!cls) return '↶ Reversible';
  if (cls.includes('IRREVERSIBLE'))  return '× Irreversible';
  if (cls.includes('PARTIALLY'))     return '△ Partial';
  if (cls.includes('STATE_RESTORE')) return '◐ Restorable';
  return '↶ Reversible';
}

function resourcePath(args: Record<string, any>) {
  return args?.path ?? args?.target_path ?? args?.table_name ?? '';
}

function isDestructive(action: ActionItem) {
  const s = action.risk_assessment?.score;
  const t = action.tool_name?.toLowerCase() ?? '';
  return s === 'HIGH' || s === 'CRITICAL' || t.includes('delete') || t.includes('drop');
}

/* ------------------------------------------------------------------ types */

interface ActionTimelineProps {
  actions: ActionItem[];
  onInspect: (action: ActionItem) => void;
  onRollback: (stepIndex: number) => void;
  onRunDemo?: () => void;
  demoRunning?: boolean;
}

/* ------------------------------------------------------------------ component */

export const ActionTimeline: React.FC<ActionTimelineProps> = ({
  actions,
  onInspect,
  onRollback,
  onRunDemo,
  demoRunning,
}) => {
  /* --- empty state --- */
  if (!actions || actions.length === 0) {
    return (
      <div className="empty-state">
        <span className="empty-icon">⏱</span>
        <p className="empty-title">Your Agent Is Ready</p>
        <p className="empty-description">
          Run the demo to watch an agent execute, checkpoint, mutate, and rewind in real time.
        </p>
        {onRunDemo && (
          <button
            className="btn btn-primary btn-md"
            onClick={onRunDemo}
            disabled={demoRunning}
            aria-label="Run interactive demo"
          >
            {demoRunning ? 'Running…' : '▶  Run Demo'}
          </button>
        )}
      </div>
    );
  }

  /* --- timeline --- */
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        /* We draw the spine as a left border on the gutter column */
      }}
    >
      {actions.map((act, idx) => {
        const destructive   = isDestructive(act);
        const hasCheckpoint = !!act.checkpoint_id;
        const isLast        = idx === actions.length - 1;

        /* Dot colour */
        const dotBg     = hasCheckpoint ? 'var(--cyan)'   : destructive ? 'var(--red-dim)' : 'var(--surface-overlay)';
        const dotBorder = hasCheckpoint ? 'var(--cyan)'   : destructive ? 'var(--red)'     : 'var(--border-strong)';
        const dotGlow   = hasCheckpoint ? '0 0 10px rgba(34,211,238,0.55)' : destructive ? '0 0 8px rgba(248,113,113,0.4)' : 'none';

        return (
          <div key={act.action_id || idx} style={{ display: 'flex', gap: 0 }}>
            {/* ── GUTTER (spine + dot) ── */}
            <div
              style={{
                width: 32,
                flexShrink: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
              }}
            >
              {/* Top connector (hidden for first item) */}
              <div
                style={{
                  width: 1,
                  height: 20,
                  background: idx === 0 ? 'transparent' : 'var(--border-default)',
                  flexShrink: 0,
                }}
              />

              {/* The dot */}
              <div
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: dotBg,
                  border: `2px solid ${dotBorder}`,
                  boxShadow: dotGlow,
                  flexShrink: 0,
                  zIndex: 1,
                  transition: 'box-shadow 0.2s ease',
                }}
              />

              {/* Bottom connector (hidden for last item) */}
              <div
                style={{
                  width: 1,
                  flex: 1,
                  minHeight: 12,
                  background: isLast ? 'transparent' : 'var(--border-default)',
                }}
              />
            </div>

            {/* ── CONTENT ── */}
            <div style={{ flex: 1, paddingBottom: isLast ? 0 : 8, paddingTop: 12 }}>
              {/* Checkpoint header row */}
              {hasCheckpoint && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                    marginTop: -4,
                  }}
                >
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      letterSpacing: '0.07em',
                      textTransform: 'uppercase',
                      color: 'var(--cyan)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                    }}
                  >
                    ◆ Checkpoint
                  </span>
                  <div
                    style={{
                      flex: 1,
                      height: 1,
                      background: 'linear-gradient(to right, var(--cyan-border), transparent)',
                    }}
                  />
                </div>
              )}

              {/* Action card */}
              <div
                className={`action-card${destructive ? ' destructive' : ''}`}
                style={{ marginBottom: 0 }}
              >
                {/* Top row: step + badges */}
                <div className="card-top">
                  <span className="card-step-id mono">
                    STEP {String(act.step_index).padStart(2, '0')}
                  </span>
                  <div className="card-badges">
                    <span className={`risk-badge ${riskClass(act.risk_assessment?.score)}`}>
                      {act.risk_assessment?.score ?? 'LOW'}
                    </span>
                    <span className="rev-badge">
                      {revLabel(act.reversibility_class)}
                    </span>
                  </div>
                </div>

                {/* Tool + resource */}
                <div className="card-tool">
                  <span className="card-tool-name">{act.tool_name}</span>
                  {resourcePath(act.arguments) && (
                    <span className="card-resource">
                      {resourcePath(act.arguments)}
                    </span>
                  )}
                </div>

                {/* Reasoning */}
                {act.reasoning && (
                  <p className="card-reasoning">{act.reasoning}</p>
                )}

                {/* Footer */}
                <div className="card-footer">
                  <span className={`card-status${act.status === 'FAILED' ? ' failed' : ''}`}>
                    {act.status === 'COMMITTED' && '✓ Committed'}
                    {act.status === 'FAILED'    && '✗ Failed'}
                    {act.status !== 'COMMITTED' && act.status !== 'FAILED' && act.status}
                  </span>
                  <div className="card-actions">
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => onInspect(act)}
                      aria-label={`Inspect action at step ${act.step_index}`}
                    >
                      Inspect
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => onRollback(act.step_index)}
                      aria-label={`Rewind workspace to step ${act.step_index}`}
                    >
                      Rewind here
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};
