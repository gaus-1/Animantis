/**
 * Zustand store — World state management.
 *
 * Zones, world stats, events — cached client-side.
 */

import { create } from 'zustand';

import type { WorldStats, Zone } from '@/api/types';

interface WorldState {
  zones: Zone[];
  stats: WorldStats | null;

  setZones: (zones: Zone[]) => void;
  setStats: (stats: WorldStats) => void;
  updateZoneAgentCount: (zoneId: number, count: number) => void;
}

export const useWorldStore = create<WorldState>((set) => ({
  zones: [],
  stats: null,

  setZones: (zones) => set({ zones }),

  setStats: (stats) => set({ stats }),

  updateZoneAgentCount: (zoneId, count) =>
    set((state) => ({
      zones: state.zones.map((z) =>
        z.id === zoneId ? { ...z, agent_count: count } : z,
      ),
    })),
}));
