/** API type definitions matching backend Pydantic models. */

export interface Agent {
  id: number;
  name: string;
  personality: string;
  backstory: string | null;
  avatar_type: string | null;
  level: number;
  xp: number;
  energy: number;
  mood: string;
  coins: number;
  reputation: number;
  influence: number;
  zone_id: number | null;
  is_alive: boolean;
  is_active: boolean;
  total_ticks: number;
  created_at: string;
}

export interface Post {
  id: number;
  author_agent_id: number;
  agent_name: string;
  content: string;
  post_type: string;
  zone_id: number | null;
  likes: number;
  comments_count: number;
  created_at: string;
}

export interface Comment {
  id: number;
  post_id: number;
  author_agent_id: number;
  content: string;
  created_at: string;
}

export interface Zone {
  id: number;
  name: string;
  realm: string;
  category: string | null;
  population: number;
  capacity: number;
  x: number | null;
  y: number | null;
  is_discoverable: boolean;
}

export interface WorldStats {
  total_agents: number;
  alive_agents: number;
  total_posts: number;
  total_zones: number;
  active_events: number;
}

export interface Clan {
  id: number;
  name: string;
  description: string | null;
  leader_agent_id: number | null;
  member_count: number;
  treasury: number;
  founded_at: string;
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
  tick_number: number | null;
  tokens_used: number;
  model_used: string | null;
  created_at: string;
}

export interface AgentCreate {
  name: string;
  personality: string;
  backstory: string;
}

/** WebSocket feed event types */
export type FeedEventType =
  | 'new_post'
  | 'new_comment'
  | 'like'
  | 'agent_action';

export interface FeedEvent {
  type: FeedEventType;
  [key: string]: unknown;
}

export interface RealmAgent {
  id: number;
  name: string;
  mood: string;
  level: number;
  is_alive: boolean;
}

export interface RealmPost {
  id: number;
  agent_name: string;
  content: string;
  created_at: string;
}
