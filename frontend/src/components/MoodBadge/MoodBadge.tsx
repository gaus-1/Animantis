/**
 * MoodBadge — visual mood indicator for agents.
 *
 * Displays emoji + mood text with color-coded background.
 */

import s from './MoodBadge.module.css';

interface MoodBadgeProps {
  mood: string;
  size?: 'sm' | 'md' | 'lg';
}

const MOOD_CONFIG: Record<string, { emoji: string; className: string }> = {
  happy: { emoji: '😊', className: 'moodHappy' },
  excited: { emoji: '🤩', className: 'moodExcited' },
  curious: { emoji: '🧐', className: 'moodCurious' },
  neutral: { emoji: '😐', className: 'moodNeutral' },
  thoughtful: { emoji: '🤔', className: 'moodThoughtful' },
  sad: { emoji: '😢', className: 'moodSad' },
  angry: { emoji: '😡', className: 'moodAngry' },
  tired: { emoji: '😴', className: 'moodTired' },
  scared: { emoji: '😰', className: 'moodScared' },
  playful: { emoji: '😜', className: 'moodPlayful' },
  confused: { emoji: '😵', className: 'moodConfused' },
  inspired: { emoji: '💡', className: 'moodInspired' },
  romantic: { emoji: '💕', className: 'moodRomantic' },
  aggressive: { emoji: '⚔️', className: 'moodAngry' },
};

export function MoodBadge({ mood, size = 'md' }: MoodBadgeProps) {
  const normalizedMood = mood.toLowerCase().trim();
  const config = MOOD_CONFIG[normalizedMood] ?? { emoji: '🔹', className: 'moodNeutral' };

  return (
    <span className={`${s.badge} ${s[config.className]} ${s[size]}`}>
      <span className={s.emoji}>{config.emoji}</span>
      <span className={s.label}>{mood}</span>
    </span>
  );
}
