"use client";

import { useEffect, useRef, useCallback } from "react";
import { getToken } from "@/lib/auth";

type NotificationPayload = {
  tytul: string;
  tresc: string;
  typ: string;
};

type WsMessage =
  | { type: "connected"; user_id: string }
  | { type: "pong" }
  | { type: "notification"; data: NotificationPayload };

const WS_BASE =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/^http/, "ws").replace(/\/api$/, "") + "/ws"
    : "";

const PING_INTERVAL = 30_000;
const RECONNECT_DELAY = 5_000;

export function useNotificationSocket(
  onNotification: (n: NotificationPayload) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const onNotificationRef = useRef(onNotification);
  onNotificationRef.current = onNotification;

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    const token = getToken();
    if (!token || !WS_BASE) return;

    const url = `${WS_BASE}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
      }, PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type === "notification") {
          onNotificationRef.current(msg.data);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      if (pingRef.current) clearInterval(pingRef.current);
      if (mountedRef.current) {
        reconnectRef.current = setTimeout(connect, RECONNECT_DELAY);
      }
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (pingRef.current) clearInterval(pingRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
