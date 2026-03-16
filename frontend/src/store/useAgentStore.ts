/**
 * Zustand store — Agent state management.
 *
 * Manages current user's agents locally for instant UI updates.
 * Server data comes via TanStack Query; this store holds
 * client-side mutations and optimistic updates.
 */

import { create } from 'zustand';

import type { Agent } from '@/api/types';

interface AgentState {
  /** Currently selected agent (for profile/chat). */
  selectedAgentId: number | null;

  /** User's agents (cached from API). */
  agents: Agent[];

  /** Actions */
  setAgents: (agents: Agent[]) => void;
  selectAgent: (id: number | null) => void;
  updateAgent: (id: number, patch: Partial<Agent>) => void;
  removeAgent: (id: number) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  selectedAgentId: null,
  agents: [],

  setAgents: (agents) => set({ agents }),

  selectAgent: (id) => set({ selectedAgentId: id }),

  updateAgent: (id, patch) =>
    set((state) => ({
      agents: state.agents.map((a) =>
        a.id === id ? { ...a, ...patch } : a,
      ),
    })),

  removeAgent: (id) =>
    set((state) => ({
      agents: state.agents.filter((a) => a.id !== id),
      selectedAgentId:
        state.selectedAgentId === id ? null : state.selectedAgentId,
    })),
}));
