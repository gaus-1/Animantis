/**
 * AgentCard — compact agent card for lists and sidebars.
 *
 * Shows avatar, name, level, energy bar, mood badge.
 */

import { Link } from 'react-router-dom';

import type { Agent } from '@/api/types';
import { EnergyBar } from '@/components/EnergyBar/EnergyBar';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';

import s from './AgentCard.module.css';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <Link to={`/agent/${agent.id}`} className={s.card}>
      <img
        src="/assets/agent-avatar.svg"
        alt={agent.name}
        className={s.avatar}
      />
      <div className={s.info}>
        <div className={s.top}>
          <span className={s.name}>{agent.name}</span>
          <span className={s.level}>Lv.{agent.level}</span>
        </div>
        <div className={s.stats}>
          <MoodBadge mood={agent.mood || 'neutral'} size="sm" />
          <span className={s.coins}>💰 {agent.coins}</span>
        </div>
        <EnergyBar energy={agent.energy} showLabel={false} size="sm" />
      </div>
    </Link>
  );
}
