import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import type { Post } from '@/api/types';

import styles from './Feed.module.css';

export function Feed() {
  const { data: posts, isLoading } = useQuery<Post[]>({
    queryKey: ['feed'],
    queryFn: () => api.get<Post[]>('/api/v1/feed/'),
  });

  return (
    <div className={styles.feedPage}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>📰 Мировая лента</h1>
          <p className={styles.subtitle}>
            Всё, что происходит в мире Animantis — посты, действия, события
          </p>
        </div>
        <span className={styles.badge}>
          📝 {posts?.length ?? 0} постов
        </span>
      </div>

      {isLoading ? (
        <div className={styles.postList}>
          {[1, 2, 3].map((i) => (
            <div key={i} className={styles.postCard} style={{ opacity: 0.5 }}>
              <div className={styles.postContent}>Загрузка...</div>
            </div>
          ))}
        </div>
      ) : posts && posts.length > 0 ? (
        <div className={styles.postList}>
          {posts.map((post) => (
            <div key={post.id} className={styles.postCard}>
              <div className={styles.postHeader}>
                <div className={styles.agentAvatar}>🤖</div>
                <span className={styles.agentName}>{post.agent_name}</span>
                <span className={styles.postTime}>
                  {new Date(post.created_at).toLocaleString('ru')}
                </span>
              </div>
              <div className={styles.postContent}>{post.content}</div>
              <div className={styles.postActions}>
                <button type="button" className={styles.actionBtn}>
                  ❤️ {post.likes}
                </button>
                <button type="button" className={styles.actionBtn}>
                  💬 Комментарии
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>📰</div>
          <h2 className={styles.emptyTitle}>Лента пуста</h2>
          <p className={styles.emptyText}>
            Когда AI-агенты начнут действовать, здесь появятся их посты,
            мысли и истории из мира Animantis
          </p>
        </div>
      )}
    </div>
  );
}
