import React from 'react';

interface HeaderProps {
  sessionId: string | null;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ sessionId, isConnected }) => {
  return (
    <header className="header">
      <div className="header-title">
        <span style={{ color: 'var(--accent-cyan)' }}>⏪ REWIND</span>
        <span style={{ color: 'var(--text-muted)' }}>|</span>
        <span>Ctrl+Z for AI Agents</span>
      </div>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        {sessionId && <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Session: {sessionId.slice(0, 8)}...</span>}
        <span className={`badge ${isConnected ? 'badge-green' : 'badge-amber'}`}>
          {isConnected ? 'LIVE TELEMETRY STREAM' : 'OFFLINE'}
        </span>
      </div>
    </header>
  );
};
