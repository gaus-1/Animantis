/**
 * TanStack Query hooks for server state.
 *
 * Each hook wraps an API call with:
 * - Caching (staleTime: 30s)
 * - Auto-refetch on window focus
 * - Loading/error states
 * - Type safety
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { api } from '@/api/client';
import type { Agent, AgentCreate, ChatResponse, Post, WorldStats, Zone } from '@/api/types';

const STALE_30S = 30_000;

// ── Agents ────────────────────────────────────────────────────

export function useMyAgents() {
  return useQuery({
    queryKey: ['agents', 'mine'],
    queryFn: () => api.get<Agent[]>('/api/v1/agents/'),
    staleTime: STALE_30S,
  });
}

export function useAgent(id: string | undefined) {
  return useQuery({
    queryKey: ['agents', id],
    queryFn: () => api.get<Agent>(`/api/v1/agents/${id}`),
    enabled: !!id,
    staleTime: STALE_30S,
  });
}

export function useCreateAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AgentCreate) =>
      api.post<Agent>('/api/v1/agents/', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

// ── Feed ──────────────────────────────────────────────────────

export function useGlobalFeed(limit = 20) {
  return useQuery({
    queryKey: ['feed', 'global', limit],
    queryFn: () => api.get<Post[]>(`/api/v1/feed/?limit=${limit}`),
    staleTime: STALE_30S,
  });
}

// ── World ─────────────────────────────────────────────────────

export function useWorldStats() {
  return useQuery({
    queryKey: ['world', 'stats'],
    queryFn: () => api.get<WorldStats>('/api/v1/world/stats'),
    staleTime: STALE_30S,
  });
}

export function useWorldZones() {
  return useQuery({
    queryKey: ['world', 'zones'],
    queryFn: () => api.get<Zone[]>('/api/v1/world/zones'),
    staleTime: STALE_30S,
  });
}

// ── Chat ──────────────────────────────────────────────────────

export function useChatMutation(agentId: string | undefined) {
  return useMutation({
    mutationFn: (message: string) =>
      api.post<ChatResponse>(`/api/v1/chat/${agentId}`, { message }),
  });
}
