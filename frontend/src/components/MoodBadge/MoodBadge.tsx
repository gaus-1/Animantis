/**
 * MoodBadge — displays agent mood as a styled Mantine Badge.
 */

import { Badge } from '@mantine/core';

const MOOD_MAP: Record<string, { emoji: string; label: string; color: string }> = {
  happy: { emoji: '😊', label: 'Счастлив', color: 'green' },
  sad: { emoji: '😢', label: 'Грустит', color: 'blue' },
  angry: { emoji: '😡', label: 'Злится', color: 'red' },
  neutral: { emoji: '😐', label: 'Спокоен', color: 'gray' },
  excited: { emoji: '🤩', label: 'Возбуждён', color: 'yellow' },
  anxious: { emoji: '😰', label: 'Тревожен', color: 'orange' },
  inspired: { emoji: '💡', label: 'Вдохновлён', color: 'violet' },
  tired: { emoji: '😴', label: 'Устал', color: 'gray' },
  curious: { emoji: '🧐', label: 'Любопытен', color: 'cyan' },
  romantic: { emoji: '😍', label: 'Влюблён', color: 'pink' },
};

interface MoodBadgeProps {
  mood: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
}

export function MoodBadge({ mood, size = 'md' }: MoodBadgeProps) {
  const config = MOOD_MAP[mood] ?? MOOD_MAP.neutral;

  return (
    <Badge
      variant="light"
      color={config.color}
      size={size}
      leftSection={config.emoji}
    >
      {config.label}
    </Badge>
  );
}
