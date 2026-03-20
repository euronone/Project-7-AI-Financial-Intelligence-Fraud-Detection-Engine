"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { Socket } from "socket.io-client";
import { connectSocket, disconnectSocket, getSocket } from "@/lib/socket";
import { useAuthStore } from "@/stores/auth-store";

interface SocketEvent {
  name: string;
  data: unknown;
  timestamp: number;
}

interface UseSocketReturn {
  socket: Socket | null;
  isConnected: boolean;
  lastEvent: SocketEvent | null;
}

const TRACKED_EVENTS = [
  "new_alert",
  "alert_updated",
  "new_transaction",
  "transaction_flagged",
  "metrics_update",
  "model_status",
] as const;

export function useSocket(): UseSocketReturn {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<SocketEvent | null>(null);
  const socketRef = useRef<Socket | null>(null);

  const handleEvent = useCallback((name: string) => {
    return (data: unknown) => {
      setLastEvent({ name, data, timestamp: Date.now() });
    };
  }, []);

  useEffect(() => {
    if (!accessToken) return;

    const s = connectSocket(accessToken);
    socketRef.current = s;

    const onConnect = () => setIsConnected(true);
    const onDisconnect = () => setIsConnected(false);

    s.on("connect", onConnect);
    s.on("disconnect", onDisconnect);

    const handlers = TRACKED_EVENTS.map((event) => {
      const handler = handleEvent(event);
      s.on(event, handler);
      return { event, handler };
    });

    return () => {
      s.off("connect", onConnect);
      s.off("disconnect", onDisconnect);
      handlers.forEach(({ event, handler }) => s.off(event, handler));
      disconnectSocket();
      socketRef.current = null;
      setIsConnected(false);
    };
  }, [accessToken, handleEvent]);

  return {
    socket: socketRef.current ?? (accessToken ? getSocket() : null),
    isConnected,
    lastEvent,
  };
}
