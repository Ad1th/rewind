import { useEffect, useState } from 'react';

export interface TelemetryEvent {
  event_id: string;
  sequence_number: number;
  session_id: string;
  action_id?: string;
  event_type: string;
  timestamp: string;
  payload: Record<string, any>;
}

export function useTelemetry(session_id: string | null) {
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  useEffect(() => {
    if (!session_id) return;

    const wsUrl = `ws://localhost:8000/api/v1/sessions/${session_id}/stream`;
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      setIsConnected(true);
    };

    socket.onmessage = (event) => {
      try {
        const parsed: TelemetryEvent = JSON.parse(event.data);
        if (parsed.event_type) {
          setEvents((prev) => [...prev, parsed]);
        }
      } catch (err) {
        console.error('Failed to parse telemetry message:', err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      socket.close();
    };
  }, [session_id]);

  return { events, isConnected };
}
