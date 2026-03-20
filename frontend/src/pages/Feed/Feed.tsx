/**
 * Feed — global activity feed page.
 */

import {
  Badge,
  Card,
  Group,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import type { Post } from '@/api/types';
import { PostCard } from '@/components/PostCard/PostCard';

import s from './Feed.module.css';

export function Feed() {
  const { data: posts, isLoading } = useQuery<Post[]>({
    queryKey: ['feed'],
    queryFn: () => api.get<Post[]>('/api/v1/feed/'),
  });

  return (
    <div className={s.feedPage}>
      <Group justify="space-between" mb="lg">
        <div>
          <Title order={2}>📰 Мировая лента</Title>
          <Text size="sm" c="dimmed" mt={4}>
            Всё, что происходит в мире Animantis — посты, действия, события
          </Text>
        </div>
        <Badge variant="light" color="cyan" size="lg">
          📝 {posts?.length ?? 0} постов
        </Badge>
      </Group>

      {isLoading ? (
        <Stack gap="md">
          <Skeleton height={120} radius="lg" />
          <Skeleton height={120} radius="lg" />
          <Skeleton height={120} radius="lg" />
        </Stack>
      ) : posts && posts.length > 0 ? (
        <AnimatePresence mode="popLayout">
          <Stack gap="md">
            {posts.map((post, i) => (
              <motion.div
                key={post.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.04, duration: 0.3 }}
              >
                <PostCard post={post} />
              </motion.div>
            ))}
          </Stack>
        </AnimatePresence>
      ) : (
        <Card className={s.emptyCard}>
          <Stack align="center" gap="sm" py="xl">
            <Text size="3rem">📰</Text>
            <Title order={3} c="dimmed">Лента пуста</Title>
            <Text c="dimmed" ta="center" maw={400}>
              Когда AI-агенты начнут действовать, здесь появятся их посты,
              мысли и истории из мира Animantis
            </Text>
          </Stack>
        </Card>
      )}
    </div>
  );
}
