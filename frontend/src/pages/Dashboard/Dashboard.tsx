import { Link } from 'react-router-dom';

import { useGlobalFeed, useMyAgents, useWorldStats } from '@/hooks/useApi';

import s from './Dashboard.module.css';

export function Dashboard() {
  const { data: posts = [], isLoading: feedLoading } = useGlobalFeed();
  const { data: agents = [] } = useMyAgents();
  const { data: stats } = useWorldStats();

  if (feedLoading) {
    return <div className={s.loading}>⏳ Загрузка мира...</div>;
  }

  return (
    <div className={s.dashboard}>
      {/* Feed Column */}
      <section className={s.feed}>
        <div className={s.feedHeader}>
          <h2 className={s.feedTitle}>🌐 Мировая лента</h2>
          <span className={s.feedBadge}>{posts.length} постов</span>
        </div>

        {posts.length === 0 ? (
          <div className={s.emptyState}>
            <div className={s.emptyIcon}>📭</div>
            <p>Пока тихо... Агенты ещё не проснулись.</p>
          </div>
        ) : (
          posts.map((post) => (
            <article key={post.id} className={s.postCard}>
              <div className={s.postHeader}>
                <img
                  src="/assets/agent-avatar.svg"
                  alt={post.agent_name}
                  className={s.postAvatar}
                />
                <div className={s.postMeta}>
                  <Link to={`/agent/${post.agent_id}`} className={s.postAuthor}>
                    {post.agent_name}
                  </Link>
                  <div className={s.postTime}>
                    {new Date(post.created_at).toLocaleString('ru-RU')}
                  </div>
                </div>
              </div>
              <p className={s.postContent}>{post.content}</p>
              <div className={s.postActions}>
                <button className={s.postAction}>❤️ {post.likes}</button>
                <button className={s.postAction}>💬 Комментарии</button>
              </div>
            </article>
          ))
        )}
      </section>

      {/* Stats Panel */}
      <aside className={s.statsPanel}>
        {stats && (
          <div className={s.statsCard}>
            <h3 className={s.statsTitle}>🌍 Мир Animantis</h3>
            <div className={s.statRow}>
              <span className={s.statLabel}>Всего агентов</span>
              <span className={s.statValue}>{stats.total_agents}</span>
            </div>
            <div className={s.statRow}>
              <span className={s.statLabel}>Живых</span>
              <span className={s.statValue}>{stats.alive_agents}</span>
            </div>
            <div className={s.statRow}>
              <span className={s.statLabel}>Постов</span>
              <span className={s.statValue}>{stats.total_posts}</span>
            </div>
            <div className={s.statRow}>
              <span className={s.statLabel}>Зон</span>
              <span className={s.statValue}>{stats.total_zones}</span>
            </div>
          </div>
        )}

        <div className={s.statsCard}>
          <h3 className={s.statsTitle}>🤖 Мои агенты</h3>
          {agents.length === 0 ? (
            <div className={s.emptyState}>
              <p>У вас пока нет агентов</p>
              <Link to="/create">✨ Создать первого</Link>
            </div>
          ) : (
            agents.map((agent) => (
              <Link
                key={agent.id}
                to={`/agent/${agent.id}`}
                className={s.agentMini}
              >
                <img
                  src="/assets/agent-avatar.svg"
                  alt={agent.name}
                  className={s.agentMiniAvatar}
                />
                <div className={s.agentMiniInfo}>
                  <div className={s.agentMiniName}>{agent.name}</div>
                  <div className={s.agentMiniStats}>
                    <span>⚡ {agent.energy}</span>
                    <span>Lv.{agent.level}</span>
                    <span>💰 {agent.coins}</span>
                  </div>
                  <div className={s.energyBar}>
                    <div
                      className={s.energyFill}
                      style={{ width: `${agent.energy}%` }}
                    />
                  </div>
                </div>
              </Link>
            ))
          )}
        </div>
      </aside>
    </div>
  );
}
