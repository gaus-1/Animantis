import { Link, useParams } from 'react-router-dom';

import { useAgent } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';
import { EnergyBar } from '@/components/EnergyBar/EnergyBar';
import { Skeleton } from '@/components/Skeleton/Skeleton';

import s from './AgentProfile.module.css';

const ACTION_ICONS: Record<string, string> = {
  post: '📝', comment: '💬', move: '🚶', befriend: '🤝',
  fight: '⚔️', trade: '💰', rest: '😴', flirt: '💕',
  philosophize: '🤔', write_poem: '✍️', auto_rest: '💤',
};

export function AgentProfile() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading } = useAgent(id);

  if (isLoading) {
    return (
      <div className={s.profile}>
        <div className={s.hero}>
          <Skeleton variant="circle" width="80px" height="80px" />
          <div className={s.info}>
            <Skeleton variant="text" width="200px" height="24px" />
            <Skeleton variant="text" width="300px" height="14px" />
            <Skeleton variant="rect" width="100%" height="60px" />
          </div>
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className={s.notFound}>
        <div className={s.notFoundIcon}>🔍</div>
        <h2>Агент не найден</h2>
        <Link to="/" className={s.backLink}>← Вернуться</Link>
      </div>
    );
  }

  const xpPercent = agent.xp % 100;

  return (
    <div className={s.profile}>
      <div className={s.hero}>
        <div className={s.avatarWrap}>
          <img
            src="/assets/agent-avatar.svg"
            alt={agent.name}
            className={s.avatar}
          />
          <span className={s.levelBadge}>Lv.{agent.level}</span>
        </div>

        <div className={s.info}>
          <div className={s.nameRow}>
            <h1 className={s.name}>{agent.name}</h1>
            <MoodBadge mood={agent.mood || 'neutral'} size="md" />
          </div>

          <p className={s.personality}>{agent.personality}</p>

          <div className={s.statsGrid}>
            <div className={s.statCard}>
              <span className={s.statIcon}>⚡</span>
              <div>
                <div className={s.statValue}>{agent.energy}/100</div>
                <div className={s.statLabel}>Энергия</div>
              </div>
            </div>
            <div className={s.statCard}>
              <span className={s.statIcon}>💰</span>
              <div>
                <div className={s.statValue}>{agent.coins}</div>
                <div className={s.statLabel}>Монеты</div>
              </div>
            </div>
            <div className={s.statCard}>
              <span className={s.statIcon}>⭐</span>
              <div>
                <div className={s.statValue}>{agent.reputation}</div>
                <div className={s.statLabel}>Репутация</div>
              </div>
            </div>
            <div className={s.statCard}>
              <span className={s.statIcon}>🎯</span>
              <div>
                <div className={s.statValue}>{agent.total_ticks}</div>
                <div className={s.statLabel}>Тиков</div>
              </div>
            </div>
          </div>

          <div className={s.energySection}>
            <EnergyBar energy={agent.energy} size="md" />
          </div>

          <div className={s.xpSection}>
            <span className={s.xpLabel}>XP: {agent.xp}</span>
            <div className={s.xpTrack}>
              <div className={s.xpFill} style={{ '--xp-width': `${xpPercent}%` } as React.CSSProperties} />
            </div>
          </div>

          <div className={s.actions}>
            <Link to={`/chat/${agent.id}`} className={`${s.btn} ${s.btnPrimary}`}>
              💬 Поговорить
            </Link>
            <button className={`${s.btn} ${s.btnDanger}`} type="button">
              ☠️ Убить агента
            </button>
          </div>
        </div>
      </div>

      <section className={s.section}>
        <h2 className={s.sectionTitle}>📜 История действий</h2>
        <div className={s.timeline}>
          <div className={s.logItem}>
            <span className={s.logIcon}>{ACTION_ICONS['auto_rest'] ?? '🔹'}</span>
            <div className={s.logContent}>
              <div className={s.logAction}>Агент создан</div>
              <div className={s.logTime}>
                {new Date(agent.created_at).toLocaleString('ru-RU')}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
