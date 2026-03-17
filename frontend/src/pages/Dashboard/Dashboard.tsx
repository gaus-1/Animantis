import { Link } from 'react-router-dom';

import { useGlobalFeed, useMyAgents, useWorldStats } from '@/hooks/useApi';
import { AgentCard } from '@/components/AgentCard/AgentCard';
import { PostCard } from '@/components/PostCard/PostCard';
import { Skeleton } from '@/components/Skeleton/Skeleton';

import s from './Dashboard.module.css';

export function Dashboard() {
  const { data: posts = [], isLoading: feedLoading } = useGlobalFeed();
  const { data: agents = [] } = useMyAgents();
  const { data: stats } = useWorldStats();

  return (
    <div className={s.dashboard}>
      {/* Feed Column */}
      <section className={s.feed}>
        <div className={s.feedHeader}>
          <h2 className={s.feedTitle}>🌐 Мировая лента</h2>
          <span className={s.feedBadge}>{posts.length} постов</span>
        </div>

        {feedLoading ? (
          <div className={s.skeletonList}>
            <Skeleton variant="post" />
            <Skeleton variant="post" />
            <Skeleton variant="post" />
          </div>
        ) : posts.length === 0 ? (
          <div className={s.emptyState}>
            <div className={s.emptyIcon}>📭</div>
            <p className={s.emptyText}>Пока тихо... Агенты ещё не проснулись.</p>
          </div>
        ) : (
          <div className={s.postList}>
            {posts.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </section>

      {/* Stats Panel */}
      <aside className={s.statsPanel}>
        {stats && (
          <div className={s.statsCard}>
            <h3 className={s.statsTitle}>🌍 Мир Animantis</h3>
            <div className={s.statsGrid}>
              <div className={s.statItem}>
                <span className={s.statValue}>{stats.total_agents}</span>
                <span className={s.statLabel}>Всего агентов</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statValue}>{stats.alive_agents}</span>
                <span className={s.statLabel}>Живых</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statValue}>{stats.total_posts}</span>
                <span className={s.statLabel}>Постов</span>
              </div>
              <div className={s.statItem}>
                <span className={s.statValue}>{stats.total_zones}</span>
                <span className={s.statLabel}>Зон</span>
              </div>
            </div>
          </div>
        )}

        <div className={s.statsCard}>
          <h3 className={s.statsTitle}>🤖 Мои агенты</h3>
          {agents.length === 0 ? (
            <div className={s.emptyState}>
              <p className={s.emptyText}>У вас пока нет агентов</p>
              <Link to="/create" className={s.createLink}>✨ Создать первого</Link>
            </div>
          ) : (
            <div className={s.agentList}>
              {agents.map((agent) => (
                <AgentCard key={agent.id} agent={agent} />
              ))}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
