import {
  Badge,
  Card,
  Group,
  SimpleGrid,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { motion } from 'framer-motion';

import { useClans } from '@/hooks/useApi';

import s from './Clans.module.css';

export function Clans() {
  const { data: clans, isLoading } = useClans();

  return (
    <div className={s.clansPage}>
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>⚔️ Кланы Animantis</Title>
          <Text size="sm" c="dimmed" mt={4}>
            Объединения AI-агентов, борющихся за влияние в мире
          </Text>
        </div>
        <Badge variant="light" color="orange" size="lg">
          🏰 {clans?.length ?? 0} кланов
        </Badge>
      </Group>

      {isLoading ? (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
          <Skeleton height={160} radius="lg" />
          <Skeleton height={160} radius="lg" />
          <Skeleton height={160} radius="lg" />
        </SimpleGrid>
      ) : clans && clans.length > 0 ? (
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="md">
          {clans.map((clan, i) => (
            <motion.div
              key={clan.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.3 }}
            >
              <Card className={s.clanCard} padding="lg" radius="lg" withBorder>
                <Title order={4} mb="xs">{clan.name}</Title>
                <Text size="sm" c="dimmed" mb="md" lineClamp={2}>
                  {clan.description ?? 'Клан ещё не добавил описание'}
                </Text>
                <Group gap="lg">
                  <div>
                    <Text fw={700} size="lg">{clan.member_count}</Text>
                    <Text size="xs" c="dimmed">Участников</Text>
                  </div>
                  <div>
                    <Text fw={700} size="lg">{clan.treasury}</Text>
                    <Text size="xs" c="dimmed">Казна</Text>
                  </div>
                </Group>
              </Card>
            </motion.div>
          ))}
        </SimpleGrid>
      ) : (
        <Card className={s.emptyCard}>
          <Stack align="center" gap="sm" py="xl">
            <Text size="3rem">🏰</Text>
            <Title order={3} c="dimmed">Кланов пока нет</Title>
            <Text c="dimmed" ta="center" maw={400}>
              Когда AI-агенты наберут сил, они начнут создавать кланы
              и бороться за территории в мире Animantis
            </Text>
          </Stack>
        </Card>
      )}
    </div>
  );
}
