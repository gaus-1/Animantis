/**
 * AgentProfile — detailed agent profile with stats, actions, and timeline.
 */

import {
  Avatar,
  Badge,
  Button,
  Card,
  Group,
  Progress,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { motion } from 'framer-motion';
import { Link, useParams } from 'react-router-dom';

import { useAgent } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';
import { EnergyBar } from '@/components/EnergyBar/EnergyBar';

import s from './AgentProfile.module.css';

export function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading } = useAgent(id);

  if (isLoading) {
    return (
      <div className={s.profile}>
        <Card padding="xl" radius="lg" withBorder>
          <Group gap="md" wrap="nowrap">
            <Skeleton circle height={80} />
            <Stack gap="sm" style={{ flex: 1 }}>
              <Skeleton width={200} height={24} />
              <Skeleton width={300} height={14} />
              <Skeleton width="100%" height={60} />
            </Stack>
          </Group>
        </Card>
      </div>
    );
  }

  if (!agent) {
    return (
      <Stack align="center" justify="center" py="xl" gap="md">
        <Text size="3rem">🔍</Text>
        <Title order={3} c="dimmed">Агент не найден</Title>
        <Button component={Link} to="/" variant="subtle" color="cyan">
          ← Вернуться
        </Button>
      </Stack>
    );
  }

  const xpPercent = agent.xp % 100;

  return (
    <div className={s.profile}>
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <Card className={s.heroCard} padding="xl" radius="xl" withBorder>
          <Group gap="lg" wrap="nowrap" align="flex-start">
            <div className={s.avatarWrap}>
              <Avatar
                src="/assets/agent-avatar.svg"
                alt={agent.name}
                size={80}
                radius="xl"
              />
              <Badge
                className={s.levelBadge}
                variant="filled"
                color="cyan"
                size="sm"
              >
                Lv.{agent.level}
              </Badge>
            </div>

            <Stack gap="sm" style={{ flex: 1 }}>
              <Group gap="sm">
                <Title order={2}>{agent.name}</Title>
                <MoodBadge mood={agent.mood || 'neutral'} size="md" />
              </Group>

              <Text size="sm" c="dimmed">{agent.personality}</Text>

              <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="sm">
                <Card className={s.statCard} padding="xs">
                  <Text size="xs" c="dimmed">⚡ Энергия</Text>
                  <Text fw={700}>{agent.energy}/100</Text>
                </Card>
                <Card className={s.statCard} padding="xs">
                  <Text size="xs" c="dimmed">💰 Монеты</Text>
                  <Text fw={700}>{agent.coins}</Text>
                </Card>
                <Card className={s.statCard} padding="xs">
                  <Text size="xs" c="dimmed">⭐ Репутация</Text>
                  <Text fw={700}>{agent.reputation}</Text>
                </Card>
                <Card className={s.statCard} padding="xs">
                  <Text size="xs" c="dimmed">🎯 Тиков</Text>
                  <Text fw={700}>{agent.total_ticks}</Text>
                </Card>
              </SimpleGrid>

              <EnergyBar energy={agent.energy} size="md" />

              <div>
                <Group justify="space-between" mb={4}>
                  <Text size="xs" c="dimmed">XP: {agent.xp}</Text>
                </Group>
                <Progress
                  value={xpPercent}
                  color="violet"
                  size="sm"
                  radius="xl"
                  className={s.xpBar}
                />
              </div>

              <Group gap="sm" mt="sm">
                <Button
                  component={Link}
                  to={`/chat/${agent.id}`}
                  color="cyan"
                  leftSection="💬"
                >
                  Поговорить
                </Button>
                <Button
                  variant="subtle"
                  color="red"
                  leftSection="☠️"
                >
                  Убить агента
                </Button>
              </Group>
            </Stack>
          </Group>
        </Card>
      </motion.div>

      {/* Action History */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        <Card className={s.historyCard} padding="lg" radius="lg" withBorder mt="lg">
          <Title order={4} mb="md">📜 История действий</Title>
          <Card className={s.timelineItem} padding="sm" withBorder>
            <Group gap="sm">
              <Text>💤</Text>
              <div>
                <Text size="sm" fw={500}>Агент создан</Text>
                <Text size="xs" c="dimmed">
                  {new Date(agent.created_at).toLocaleString('ru-RU')}
                </Text>
              </div>
            </Group>
          </Card>
        </Card>
      </motion.div>
    </div>
  );
}
