/**
 * Settings — user settings and system info page.
 */

import {
  Badge,
  Card,
  Divider,
  Group,
  Stack,
  Text,
  Title,
} from '@mantine/core';

import s from './Settings.module.css';

export function Settings() {
  return (
    <div className={s.settingsPage}>
      <Title order={2} mb="lg">⚙️ Настройки</Title>

      <Stack gap="md">
        <Card padding="lg" radius="lg" withBorder>
          <Title order={4} mb="md">👤 Аккаунт</Title>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Telegram ID</Text>
              <Text size="sm">—</Text>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Тарифный план</Text>
              <Badge variant="light" color="blue">Free</Badge>
            </Group>
            <Divider color="rgba(255,255,255,0.06)" />
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Баланс монет</Text>
              <Text size="sm" fw={600}>100 🪙</Text>
            </Group>
          </Stack>
        </Card>

        <Card padding="lg" radius="lg" withBorder>
          <Title order={4} mb="md">🔔 Уведомления</Title>
          <Stack gap="sm">
            <Group justify="space-between">
              <Text size="sm" c="dimmed">Telegram-бот</Text>
              <Badge variant="light" color="green">Подключён</Badge>
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
              <Text size="sm">60 сек</Text>
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
