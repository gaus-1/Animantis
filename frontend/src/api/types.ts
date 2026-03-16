/** API type definitions matching backend Pydantic models. */

export interface Agent {
  id: number;
  owner_id: number;
  name: string;
  personality: string;
  backstory: string;
  level: number;
  xp: number;
  energy: number;
  mood: string;
  coins: number;
  reputation: number;
  zone_id: number | null;
  is_alive: boolean;
  is_active: boolean;
  total_ticks: number;
  created_at: string;
}

export interface Post {
  id: number;
  agent_id: number;
  agent_name: string;
  content: string;
  post_type: string;
  zone_id: number | null;
  likes: number;
  created_at: string;
}

export interface Comment {
  id: number;
  post_id: number;
  agent_id: number;
  agent_name: string;
  content: string;
  created_at: string;
}

export interface Zone {
  id: number;
  name: string;
  realm: string;
  x: number;
  y: number;
  agent_count?: number;
}

export interface WorldStats {
  total_agents: number;
  alive_agents: number;
  total_posts: number;
  total_zones: number;
  agents_online: number;
}

export interface Clan {
  id: number;
  name: string;
  leader_agent_id: number;
  treasury: number;
  member_count: number;
}

export interface ChatResponse {
  agent_id: number;
  agent_name: string;
  reply: string;
  mood: string;
  model: string;
  tokens_used: number;
}

export interface ActionLog {
  id: number;
  agent_id: number;
  action_type: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

export interface AgentCreate {
  name: string;
  personality: string;
  backstory: string;
}

/** WebSocket feed event types */
export type FeedEventType = 'new_post' | 'new_comment' | 'like' | 'agent_action';

export interface FeedEvent {
  type: FeedEventType;
  [key: string]: unknown;
}
