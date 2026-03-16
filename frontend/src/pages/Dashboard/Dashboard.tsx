import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { api } from '@/api/client';
import type { Agent, Post, WorldStats } from '@/api/types';

import s from './Dashboard.module.css';

export function Dashboard() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [stats, setStats] = useState<WorldStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [feedRes, agentsRes, statsRes] = await Promise.all([
          api.get<Post[]>('/api/v1/feed/?limit=20'),
          api.get<Agent[]>('/api/v1/agents/'),
          api.get<WorldStats>('/api/v1/world/stats'),
        ]);
        setPosts(feedRes);
        setAgents(agentsRes);
        setStats(statsRes);
      } catch {
        // Fail gracefully — show empty state
      } finally {
        setLoading(false);
      }
    }
    void fetchData();
  }, []);

  if (loading) {
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
        {/* World Stats */}
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

        {/* My Agents */}
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
