/**
 * AgentCard — compact agent card for lists and sidebars.
 *
 * Shows avatar, name, level, energy bar, mood badge.
 * Uses Mantine Card for consistent styling.
 */

import { Badge, Card, Group, Text } from '@mantine/core';
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
    <Card
      component={Link}
      to={`/agent/${agent.id}`}
      className={s.card}
      padding="sm"
      radius="md"
      withBorder
    >
      <Group gap="sm" wrap="nowrap">
        <div className={s.avatarWrap}>
          <img
            src="/assets/agent-avatar.svg"
            alt={agent.name}
            className={s.avatar}
          />
          <span className={s.levelBadge}>Lv.{agent.level}</span>
        </div>

        <div className={s.info}>
          <Group justify="space-between" wrap="nowrap" mb={4}>
            <Text size="sm" fw={600} truncate="end" className={s.name}>
              {agent.name}
            </Text>
            <Badge variant="light" color="yellow" size="xs">
              💰 {agent.coins}
            </Badge>
          </Group>

          <MoodBadge mood={agent.mood || 'neutral'} size="xs" />

          <div className={s.energyWrap}>
            <EnergyBar energy={agent.energy} showLabel={false} size="sm" />
          </div>
        </div>
      </Group>
    </Card>
  );
}
