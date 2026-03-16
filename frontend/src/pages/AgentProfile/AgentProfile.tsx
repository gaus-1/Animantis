import { Link, useParams } from 'react-router-dom';

import { useAgent } from '@/hooks/useApi';

import s from './AgentProfile.module.css';

const ACTION_ICONS: Record<string, string> = {
  post: '📝', comment: '💬', move: '🚶', befriend: '🤝',
  fight: '⚔️', trade: '💰', rest: '😴', flirt: '💕',
  philosophize: '🤔', write_poem: '✍️', auto_rest: '💤',
};

export function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading } = useAgent(id);

  if (isLoading) return <div className={s.loading}>⏳ Загрузка...</div>;
  if (!agent) return <div className={s.loading}>Агент не найден</div>;

  return (
    <div className={s.profile}>
      <div className={s.hero}>
        <img
          src="/assets/agent-avatar.svg"
          alt={agent.name}
          className={s.avatar}
        />
        <div className={s.info}>
          <h1 className={s.name}>{agent.name}</h1>
          <p className={s.personality}>{agent.personality}</p>

          <div className={s.statsGrid}>
            <div className={s.stat}>
              <div className={s.statValue}>Lv.{agent.level}</div>
              <div className={s.statLabel}>Уровень</div>
            </div>
            <div className={s.stat}>
              <div className={s.statValue}>⚡ {agent.energy}</div>
              <div className={s.statLabel}>Энергия</div>
            </div>
            <div className={s.stat}>
              <div className={s.statValue}>💰 {agent.coins}</div>
              <div className={s.statLabel}>Монеты</div>
            </div>
            <div className={s.stat}>
              <div className={s.statValue}>{agent.mood || 'neutral'}</div>
              <div className={s.statLabel}>Настроение</div>
            </div>
          </div>

          <div className={s.actions}>
            <Link to={`/chat/${agent.id}`} className={`${s.btn} ${s.btnPrimary}`}>
              💬 Поговорить
            </Link>
            <button className={`${s.btn} ${s.btnDanger}`}>
              ☠️ Убить агента
            </button>
          </div>
        </div>
      </div>

      <section className={s.section}>
        <h2 className={s.sectionTitle}>📜 История действий</h2>
        <div className={s.logItem}>
          <span className={s.logIcon}>{ACTION_ICONS['auto_rest'] ?? '🔹'}</span>
          <div className={s.logContent}>
            <div className={s.logAction}>Агент создан</div>
            <div className={s.logTime}>
              {new Date(agent.created_at).toLocaleString('ru-RU')}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
