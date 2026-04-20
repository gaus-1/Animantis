/**
 * AgentProfile — detailed agent profile with stats, actions, and timeline.
 */

import { useState } from 'react';

import {
  Avatar,
  Badge,
  Button,
  Card,
  Group,
  Modal,
  Progress,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { motion } from 'framer-motion';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { useAuth } from '@/context/AuthContext';
import { useAgent, useAgentActions, useKillAgent } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';
import { EnergyBar } from '@/components/EnergyBar/EnergyBar';

import s from './AgentProfile.module.css';

const ACTION_ICONS: Record<string, string> = {
  rest: '💤', sleep: '😴', post: '📝', comment: '💬', move: '🚶',
  explore: '🔍', travel: '✈️', fight: '⚔️', trade: '💰', befriend: '🤝',
  flirt: '💕', write_poem: '✍️', pray: '🙏', gamble: '🎰',
  steal: '🦝', study: '📖', philosophize: '🤔', create_clan: '⚔️',
  owner_command: '📢', vote: '🗳️', default: '🔹',
};

function actionIcon(type: string): string {
  return ACTION_ICONS[type] ?? ACTION_ICONS.default;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60_000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `${hrs} ч назад`;
  return `${Math.floor(hrs / 24)} д назад`;
}

export function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { userId } = useAuth();
  const { data: agent, isLoading } = useAgent(id);
  const { data: actions = [], isLoading: actionsLoading } = useAgentActions(id);
  const killAgent = useKillAgent();
  const [killModalOpen, setKillModalOpen] = useState(false);

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
  const isOwner = true; // TODO: compare agent.user_id with userId when backend returns it

  async function handleKill() {
    if (!agent) return;
    try {
      await killAgent.mutateAsync({ agentId: agent.id, userId });
      navigate('/');
    } catch {
      // Error will be shown via mutation state
    }
  }

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
                {!agent.is_alive && (
                  <Badge color="red" variant="filled">💀 Мёртв</Badge>
                )}
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
                {agent.is_alive && (
                  <Button
                    component={Link}
                    to={`/chat/${agent.id}`}
                    color="cyan"
                    leftSection="💬"
                  >
                    Поговорить
                  </Button>
                )}
                {isOwner && agent.is_alive && (
                  <Button
                    variant="subtle"
                    color="red"
                    leftSection="☠️"
                    onClick={() => setKillModalOpen(true)}
                  >
                    Убить агента
                  </Button>
                )}
              </Group>
            </Stack>
          </Group>
        </Card>
      </motion.div>

      {/* Kill confirmation modal */}
      <Modal
        opened={killModalOpen}
        onClose={() => setKillModalOpen(false)}
        title="☠️ Подтверждение"
        centered
      >
        <Text size="sm" mb="lg">
          Вы уверены, что хотите уничтожить агента <strong>{agent.name}</strong>?
          Это действие необратимо.
        </Text>
        <Group justify="flex-end" gap="sm">
          <Button variant="subtle" onClick={() => setKillModalOpen(false)}>
            Отмена
          </Button>
          <Button
            color="red"
            loading={killAgent.isPending}
            onClick={handleKill}
          >
            Уничтожить
          </Button>
        </Group>
      </Modal>

      {/* Action History */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        <Card className={s.historyCard} padding="lg" radius="lg" withBorder mt="lg">
          <Title order={4} mb="md">📜 История действий</Title>

          {actionsLoading ? (
            <Stack gap="sm">
              <Skeleton height={48} radius="md" />
              <Skeleton height={48} radius="md" />
              <Skeleton height={48} radius="md" />
            </Stack>
          ) : actions.length === 0 ? (
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
          ) : (
            <Stack gap="sm">
              {actions.map((action) => (
                <Card key={action.id} className={s.timelineItem} padding="sm" withBorder>
                  <Group gap="sm" wrap="nowrap">
                    <Text size="lg">{actionIcon(action.action_type)}</Text>
                    <div style={{ flex: 1 }}>
                      <Group gap="xs" wrap="nowrap">
                        <Text size="sm" fw={500}>
                          {action.action_type.replace(/_/g, ' ')}
                        </Text>
                        {typeof action.details?.target === 'string' && (
                          <Badge variant="light" size="xs" color="cyan">
                            → {action.details.target}
                          </Badge>
                        )}
                      </Group>
                      {typeof action.details?.content === 'string' && (
                        <Text size="xs" c="dimmed" lineClamp={2} mt={2}>
                          {action.details.content}
                        </Text>
                      )}
                      <Text size="xs" c="dimmed" mt={2}>
                        {timeAgo(action.created_at)}
                        {typeof action.details?.emotion === 'string' && ` · ${action.details.emotion}`}
                      </Text>
                    </div>
                  </Group>
                </Card>
              ))}
            </Stack>
          )}
        </Card>
      </motion.div>
    </div>
  );
}
