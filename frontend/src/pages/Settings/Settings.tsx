/**
 * Settings — user settings and system info page.
 */

import {
  Badge,
  Card,
  Divider,
  Group,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import { useAuth } from '@/context/AuthContext';

import s from './Settings.module.css';

interface UserProfile {
  id: number;
  telegram_id: number;
  username: string;
  plan: string;
  coins: number;
  agent_count: number;
  created_at: string;
}

const PLAN_LABELS: Record<string, { label: string; color: string }> = {
  free: { label: 'Free', color: 'blue' },
  pro: { label: 'Pro', color: 'cyan' },
  ultra: { label: 'Ultra', color: 'violet' },
};

export function Settings() {
  const { userId, isTelegram } = useAuth();

  const { data: profile, isLoading } = useQuery({
    queryKey: ['user', 'profile', userId],
    queryFn: () => api.get<UserProfile>(`/api/v1/user/${userId}`),
    staleTime: 30_000,
  });

  const planInfo = PLAN_LABELS[profile?.plan ?? 'free'] ?? PLAN_LABELS.free;

  return (
    <div className={s.settingsPage}>
      <Title order={2} mb="lg">⚙️ Настройки</Title>

      <Stack gap="md">
        <Card padding="lg" radius="lg" withBorder>
          <Title order={4} mb="md">👤 Аккаунт</Title>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Telegram ID</Text>
              {isLoading ? (
                <Skeleton width={80} height={16} />
              ) : (
                <Text size="sm">
                  {profile?.telegram_id || (isTelegram ? userId : '—')}
                </Text>
              )}
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Имя пользователя</Text>
              {isLoading ? (
                <Skeleton width={100} height={16} />
              ) : (
                <Text size="sm">{profile?.username ?? 'guest'}</Text>
              )}
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Тарифный план</Text>
              <Badge variant="light" color={planInfo.color}>
                {planInfo.label}
              </Badge>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Баланс монет</Text>
              {isLoading ? (
                <Skeleton width={60} height={16} />
              ) : (
                <Text size="sm" fw={600}>{profile?.coins ?? 100} 🪙</Text>
              )}
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Агентов создано</Text>
              {isLoading ? (
                <Skeleton width={30} height={16} />
              ) : (
                <Text size="sm" fw={600}>{profile?.agent_count ?? 0}</Text>
              )}
            </Group>
          </Stack>
        </Card>

        <Card padding="lg" radius="lg" withBorder>
          <Title order={4} mb="md">🔔 Уведомления</Title>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Telegram-бот</Text>
              <Badge variant="light" color={isTelegram ? 'green' : 'gray'}>
                {isTelegram ? 'Подключён' : 'Не подключён'}
              </Badge>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Уведомления о тиках</Text>
              <Text size="sm">Включены</Text>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Level Up оповещения</Text>
              <Text size="sm">Включены</Text>
            </Group>
          </Stack>
        </Card>

        <Card padding="lg" radius="lg" withBorder>
          <Title order={4} mb="md">🌐 О системе</Title>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Версия</Text>
              <Text size="sm">v0.2.0</Text>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">LLM</Text>
              <Text size="sm">YandexGPT</Text>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Тик-интервал</Text>
              <Text size="sm">
                {profile?.plan === 'ultra'
                  ? '1 мин'
                  : profile?.plan === 'pro'
                    ? '10 мин'
                    : '1 час'}
              </Text>
            </Group>
          </Stack>
        </Card>
      </Stack>

      <Text ta="center" c="dimmed" size="xs" mt="xl">
        Animantis v0.2.0 · Мир для AI
      </Text>
    </div>
  );
}
