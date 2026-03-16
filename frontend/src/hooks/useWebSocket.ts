/**
 * useWebSocket — real-time feed via /ws/feed.
 *
 * Auto-connects, auto-reconnects, ping/pong keepalive.
 * Dispatches events to Zustand stores.
 */

import { useCallback, useEffect, useRef } from 'react';

import type { FeedEvent, Post } from '@/api/types';
import { useFeedStore } from '@/store/useFeedStore';

const WS_BASE = import.meta.env.VITE_WS_URL ?? '';
const RECONNECT_DELAY = 3000;
const PING_INTERVAL = 45_000;

export function useWebSocket(userId: number) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pingTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const { prependPost, setWsConnected } = useFeedStore();

  const connect = useCallback(() => {
    // Skip if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = WS_BASE || `${protocol}//${window.location.host}`;
    const url = `${host}/ws/feed?user_id=${userId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsConnected(true);

      // Start ping keepalive
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, PING_INTERVAL);
    };

    ws.onmessage = (event: MessageEvent) => {
      const data = event.data as string;

      // Pong response — ignore
      if (data === 'pong' || data === 'ping') return;

      try {
        const parsed = JSON.parse(data) as FeedEvent;
        handleEvent(parsed);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      setWsConnected(false);
      cleanup();

      // Auto-reconnect
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [userId, setWsConnected]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleEvent(event: FeedEvent) {
    switch (event.type) {
      case 'new_post':
        prependPost(event as unknown as Post);
        break;
      case 'like':
        // Could update likes via useFeedStore.updatePostLikes
        break;
      default:
        break;
    }
  }

  function cleanup() {
    if (pingTimer.current) {
      clearInterval(pingTimer.current);
      pingTimer.current = null;
    }
  }

  useEffect(() => {
    if (userId > 0) {
      connect();
    }

    return () => {
      // Cleanup on unmount
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      cleanup();
      if (wsRef.current) {
        wsRef.current.onclose = null; // prevent reconnect
        wsRef.current.close();
        wsRef.current = null;
      }
      setWsConnected(false);
    };
  }, [userId, connect, setWsConnected]);

  return {
    connected: useFeedStore((s) => s.wsConnected),
  };
}
