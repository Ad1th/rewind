import React from 'react';

interface HeaderProps {
  sessionId: string | null;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ sessionId, isConnected }) => {
  return (
    <header
      style={{
        borderBottom: '1px solid var(--border-color)',
        background: 'rgba(13, 17, 26, 0.75)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        padding: '16px 0',
      }}
    >
      <div
        style={{
          maxWidth: '1140px',
          margin: '0 auto',
          padding: '0 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span
                style={{
                  fontSize: '1.4rem',
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  background: 'linear-gradient(135deg, #ffffff 0%, #94a3b8 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                REWIND
              </span>
              <span
                style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--accent-cyan)',
                  background: 'rgba(0, 240, 255, 0.08)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  border: '1px solid rgba(0, 240, 255, 0.2)',
                }}
              >
                Ctrl+Z for AI Agents
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Intercept, verify, and deterministically reverse agent actions
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {sessionId && (
            <span
              className="font-mono"
              style={{ fontSize: '0.75rem', color: 'var(--text-dim)', background: '#1e293b', padding: '4px 8px', borderRadius: '6px' }}
            >
              SESSION: {sessionId.slice(0, 16)}...
            </span>
          )}

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 12px',
              borderRadius: '20px',
              background: isConnected ? 'rgba(16, 185, 129, 0.08)' : 'rgba(100, 116, 139, 0.1)',
              border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.25)' : 'rgba(100, 116, 139, 0.2)'}`,
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.04em',
              color: isConnected ? 'var(--accent-green)' : 'var(--text-muted)',
            }}
          >
            <span className={`status-dot ${isConnected ? 'live' : 'offline'}`} />
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </div>
        </div>
      </div>
    </header>
  );
};
