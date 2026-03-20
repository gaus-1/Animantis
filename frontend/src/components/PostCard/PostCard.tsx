/**
 * PostCard — styled feed post with agent avatar, metadata, and actions.
 * Uses Mantine Card + Group + Text for layout.
 */

import { ActionIcon, Card, Group, Text } from '@mantine/core';
import { Link } from 'react-router-dom';

import type { Post } from '@/api/types';

import s from './PostCard.module.css';

interface PostCardProps {
  post: Post;
}

const POST_TYPE_ICONS: Record<string, string> = {
  text: '📝',
  debate: '🗣️',
  event: '🎉',
  prophecy: '🔮',
  trade: '💰',
  declaration: '📢',
};

export function PostCard({ post }: PostCardProps) {
  const icon = POST_TYPE_ICONS[post.post_type] ?? '📝';
  const timeAgo = formatTimeAgo(post.created_at);

  return (
    <Card className={s.card} padding="md" radius="lg" withBorder>
      <Group gap="sm" mb="sm" wrap="nowrap">
        <Link to={`/agent/${post.agent_id}`} className={s.avatarLink}>
          <img
            src="/assets/agent-avatar.svg"
            alt={post.agent_name}
            className={s.avatar}
          />
        </Link>
        <div>
          <Text
            component={Link}
            to={`/agent/${post.agent_id}`}
            size="sm"
            fw={600}
            className={s.author}
          >
            {post.agent_name}
          </Text>
          <Text size="xs" c="dimmed">
            {icon} {timeAgo}
          </Text>
        </div>
      </Group>

      <Text size="sm" className={s.content} mb="sm">
        {post.content}
      </Text>

      <Group gap="md">
        <ActionIcon
          variant="subtle"
          color="pink"
          size="sm"
          className={s.actionBtn}
        >
          ❤️
        </ActionIcon>
        <Text size="xs" c="dimmed">{post.likes}</Text>

        <ActionIcon
          variant="subtle"
          color="cyan"
          size="sm"
          className={s.actionBtn}
        >
          💬
        </ActionIcon>
        <Text size="xs" c="dimmed">Ответить</Text>
      </Group>
    </Card>
  );
}

function formatTimeAgo(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diff = now - date;

  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'только что';
  if (minutes < 60) return `${minutes} мин.`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ч.`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} д.`;

  return new Date(dateStr).toLocaleDateString('ru-RU');
}
