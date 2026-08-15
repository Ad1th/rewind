'use client';
import React from 'react';

interface HeaderProps {
  sessionId: string | null;
  isConnected: boolean;
}

export const Header: React.FC<HeaderProps> = ({ sessionId, isConnected }) => (
  <header className="app-header">
    <div className="app-header-inner">
      <div className="brand-wordmark">
        <span className="name">REWIND</span>
        <span className="tagline">Ctrl+Z for AI Agents</span>
      </div>

      <div className="header-right">
        {sessionId && (
          <span className="session-pill">
            {sessionId.slice(0, 8)}…
          </span>
        )}

        <span className={`connection-badge ${isConnected ? 'live' : 'offline'}`}>
          <span className={`status-dot ${isConnected ? 'live' : 'offline'}`} />
          {isConnected ? 'Live' : 'Offline'}
        </span>
      </div>
    </div>
  </header>
);
