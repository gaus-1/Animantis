/**
 * Zustand store — Feed state management.
 *
 * Manages real-time feed updates via WebSocket + API.
 * New posts from WebSocket are prepended to the feed.
 */

import { create } from 'zustand';

import type { Post } from '@/api/types';

interface FeedState {
  /** Posts in the global feed. */
  posts: Post[];

  /** Whether WebSocket is connected. */
  wsConnected: boolean;

  /** Actions */
  setPosts: (posts: Post[]) => void;
  prependPost: (post: Post) => void;
  updatePostLikes: (postId: number, likes: number) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useFeedStore = create<FeedState>((set) => ({
  posts: [],
  wsConnected: false,

  setPosts: (posts) => set({ posts }),

  prependPost: (post) =>
    set((state) => ({
      posts: [post, ...state.posts].slice(0, 100), // keep last 100
    })),

  updatePostLikes: (postId, likes) =>
    set((state) => ({
      posts: state.posts.map((p) =>
        p.id === postId ? { ...p, likes } : p,
      ),
    })),

  setWsConnected: (connected) => set({ wsConnected: connected }),
}));
