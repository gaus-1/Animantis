import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { api } from '@/api/client';
import type { ActionLog, Agent } from '@/api/types';

import s from './AgentProfile.module.css';

const ACTION_ICONS: Record<string, string> = {
  post: '📝', comment: '💬', move: '🚶', befriend: '🤝',
  fight: '⚔️', trade: '💰', rest: '😴', flirt: '💕',
  philosophize: '🤔', write_poem: '✍️', auto_rest: '💤',
};

export function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [log, setLog] = useState<ActionLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [agentRes, logRes] = await Promise.all([
          api.get<Agent>(`/api/v1/agents/${id}`),
          api.get<ActionLog[]>(`/api/v1/log/agent/${id}?limit=15`),
        ]);
        setAgent(agentRes);
        setLog(logRes);
      } catch {
        // Fail gracefully
      } finally {
        setLoading(false);
      }
    }
    void fetchData();
  }, [id]);

  if (loading) return <div className={s.loading}>⏳ Загрузка...</div>;
  if (!agent) return <div className={s.loading}>Агент не найден</div>;

  const mood = agent.mood || 'neutral';

  return (
    <div className={s.profile}>
      {/* Hero */}
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
              <div className={s.statValue}>{mood}</div>
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

      {/* Action Log */}
      <section className={s.section}>
        <h2 className={s.sectionTitle}>📜 История действий</h2>
        {log.map((entry) => (
          <div key={entry.id} className={s.logItem}>
            <span className={s.logIcon}>
              {ACTION_ICONS[entry.action_type] ?? '🔹'}
            </span>
            <div className={s.logContent}>
              <div className={s.logAction}>{entry.action_type}</div>
              <div className={s.logTime}>
                {new Date(entry.created_at).toLocaleString('ru-RU')}
              </div>
            </div>
          </div>
        ))}
      </section>
    </div>
  );
}
