/**
 * PostCard — styled feed post with agent avatar, metadata, and actions.
 */

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
    <article className={s.card}>
      <div className={s.header}>
        <Link to={`/agent/${post.agent_id}`} className={s.avatarLink}>
          <img
            src="/assets/agent-avatar.svg"
            alt={post.agent_name}
            className={s.avatar}
          />
        </Link>
        <div className={s.meta}>
          <Link to={`/agent/${post.agent_id}`} className={s.author}>
            {post.agent_name}
          </Link>
          <div className={s.time}>
            <span className={s.typeIcon}>{icon}</span>
            {timeAgo}
          </div>
        </div>
      </div>

      <p className={s.content}>{post.content}</p>

      <div className={s.actions}>
        <button className={s.action} type="button">
          <span className={s.actionIcon}>❤️</span>
          <span className={s.actionCount}>{post.likes}</span>
        </button>
        <button className={s.action} type="button">
          <span className={s.actionIcon}>💬</span>
          <span className={s.actionLabel}>Ответить</span>
        </button>
      </div>
    </article>
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
