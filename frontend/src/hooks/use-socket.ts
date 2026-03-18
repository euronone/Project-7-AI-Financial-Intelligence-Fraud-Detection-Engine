"use client";

/**
 * Socket.IO hooks for real-time transaction feed (F1.3).
 *
 * useTransactionSocket — connects to /transactions namespace and provides:
 *   - liveTransactions: last N received transaction events
 *   - isConnected: connection state
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { getTransactionsSocket } from "@/lib/socket";
import type { LiveTransactionEvent } from "@/types/transaction";

const MAX_LIVE_ITEMS = 50;

interface UseTransactionSocketReturn {
  liveTransactions: LiveTransactionEvent[];
  isConnected: boolean;
  clearFeed: () => void;
}

export function useTransactionSocket(): UseTransactionSocketReturn {
  const [liveTransactions, setLiveTransactions] = useState<LiveTransactionEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef(getTransactionsSocket());

  const clearFeed = useCallback(() => setLiveTransactions([]), []);

  useEffect(() => {
    const socket = socketRef.current;

    function onConnect() {
      setIsConnected(true);
    }

    function onDisconnect() {
      setIsConnected(false);
    }

    function onNewTransaction(payload: LiveTransactionEvent) {
      setLiveTransactions((prev) => {
        const next = [payload, ...prev];
        return next.slice(0, MAX_LIVE_ITEMS);
      });
    }

    function onTransactionFlagged(payload: LiveTransactionEvent) {
      // Update the matching transaction in the live feed with the decision
      setLiveTransactions((prev) =>
        prev.map((t) => (t.id === payload.id ? { ...t, ...payload } : t))
      );
    }

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("new_transaction", onNewTransaction);
    socket.on("transaction_flagged", onTransactionFlagged);

    if (!socket.connected) {
      socket.connect();
    }

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("new_transaction", onNewTransaction);
      socket.off("transaction_flagged", onTransactionFlagged);
    };
  }, []);

  return { liveTransactions, isConnected, clearFeed };
}
