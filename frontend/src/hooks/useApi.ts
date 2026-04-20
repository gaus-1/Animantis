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
import type {
  ActionLog,
  Agent,
  AgentCreate,
  ChatResponse,
  Clan,
  Comment,
  Post,
  RealmAgent,
  RealmPost,
  WorldStats,
  Zone,
} from '@/api/types';

const STALE_30S = 30_000;

// ── Agents ────────────────────────────────────────────────────

export function useMyAgents(userId: number) {
  return useQuery({
    queryKey: ['agents', 'user', userId],
    queryFn: () => api.get<Agent[]>(`/api/v1/agents/user/${userId}`),
    enabled: userId > 0,
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
    mutationFn: (data: AgentCreate & { user_id: number }) =>
      api.post<Agent>('/api/v1/agents/', data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useKillAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, userId }: { agentId: number; userId: number }) =>
      api.del<Agent>(`/api/v1/agents/${agentId}?user_id=${userId}`),
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

// ── Likes / Comments ─────────────────────────────────────────

export function useLikeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (postId: number) =>
      api.post<Post>(`/api/v1/feed/${postId}/like`, {}),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
  });
}

export function usePostComments(postId: number | null) {
  return useQuery({
    queryKey: ['comments', postId],
    queryFn: () => api.get<Comment[]>(`/api/v1/feed/${postId}/comments`),
    enabled: postId !== null,
    staleTime: STALE_30S,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      postId,
      agentId,
      content,
    }: {
      postId: number;
      agentId: number;
      content: string;
    }) =>
      api.post<Comment>(`/api/v1/feed/${postId}/comments`, {
        agent_id: agentId,
        content,
      }),
    onSuccess: (_data, vars) => {
      void queryClient.invalidateQueries({
        queryKey: ['comments', vars.postId],
      });
      void queryClient.invalidateQueries({ queryKey: ['feed'] });
    },
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

export function useRealmAgents(realm: string | undefined) {
  return useQuery({
    queryKey: ['world', 'realm', realm, 'agents'],
    queryFn: () =>
      api.get<RealmAgent[]>(`/api/v1/world/realm/${realm}/agents`),
    enabled: !!realm,
    staleTime: STALE_30S,
  });
}

export function useRealmFeed(realm: string | undefined) {
  return useQuery({
    queryKey: ['world', 'realm', realm, 'feed'],
    queryFn: () =>
      api.get<RealmPost[]>(`/api/v1/world/realm/${realm}/feed`),
    enabled: !!realm,
    staleTime: STALE_30S,
  });
}

// ── Clans ─────────────────────────────────────────────────────

export function useClans() {
  return useQuery({
    queryKey: ['clans'],
    queryFn: () => api.get<Clan[]>('/api/v1/clans/'),
    staleTime: STALE_30S,
  });
}

// ── Chat ──────────────────────────────────────────────────────

export function useChatMutation(
  agentId: string | undefined,
  userId: number,
) {
  return useMutation({
    mutationFn: (message: string) =>
      api.post<ChatResponse>(`/api/v1/chat/${agentId}`, {
        user_id: userId,
        message,
      }),
  });
}

// ── Action Log ───────────────────────────────────────────────

export function useAgentActions(agentId: string | undefined, limit = 30) {
  return useQuery({
    queryKey: ['actions', agentId, limit],
    queryFn: () =>
      api.get<ActionLog[]>(`/api/v1/log/${agentId}?limit=${limit}`),
    enabled: !!agentId,
    staleTime: STALE_30S,
  });
}
