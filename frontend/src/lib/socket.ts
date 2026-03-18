/**
 * Socket.IO client singleton.
 *
 * Provides pre-configured namespace connections for:
 * - /transactions — live transaction feed
 * - /alerts       — fraud alert notifications
 * - /dashboard    — dashboard metric updates
 *
 * Connections are lazy: they only connect when first accessed and
 * can be disconnected when no longer needed.
 */
import { io, type Socket } from "socket.io-client";

const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ?? "http://localhost:8000";

function createNamespaceSocket(namespace: string): Socket {
  return io(`${WS_URL}${namespace}`, {
    autoConnect: false,       // Connect explicitly via socket.connect()
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    transports: ["websocket", "polling"],
  });
}

// Lazy singletons — one per namespace
let _transactionsSocket: Socket | null = null;
let _alertsSocket: Socket | null = null;
let _dashboardSocket: Socket | null = null;

export function getTransactionsSocket(): Socket {
  if (!_transactionsSocket) {
    _transactionsSocket = createNamespaceSocket("/transactions");
  }
  return _transactionsSocket;
}

export function getAlertsSocket(): Socket {
  if (!_alertsSocket) {
    _alertsSocket = createNamespaceSocket("/alerts");
  }
  return _alertsSocket;
}

export function getDashboardSocket(): Socket {
  if (!_dashboardSocket) {
    _dashboardSocket = createNamespaceSocket("/dashboard");
  }
  return _dashboardSocket;
}

/** Disconnect all namespace sockets — call on app unmount / sign-out. */
export function disconnectAll(): void {
  _transactionsSocket?.disconnect();
  _alertsSocket?.disconnect();
  _dashboardSocket?.disconnect();
}
