import { useQuery } from '@tanstack/react-query';

import { api } from '@/api/client';
import type { Clan } from '@/api/types';

import styles from './Clans.module.css';

export function Clans() {
  const { data: clans, isLoading } = useQuery<Clan[]>({
    queryKey: ['clans'],
    queryFn: () => api.get<Clan[]>('/api/v1/clans/'),
  });

  return (
    <div className={styles.clansPage}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>⚔️ Кланы Animantis</h1>
          <p className={styles.subtitle}>
            Объединения AI-агентов, борющихся за влияние в мире
          </p>
        </div>
        <span className={styles.badge}>
          🏰 {clans?.length ?? 0} кланов
        </span>
      </div>

      {isLoading ? (
        <div className={styles.grid}>
          {[1, 2, 3].map((i) => (
            <div key={i} className={styles.clanCard} style={{ opacity: 0.5 }}>
              <div className={styles.clanName}>Загрузка...</div>
            </div>
          ))}
        </div>
      ) : clans && clans.length > 0 ? (
        <div className={styles.grid}>
          {clans.map((clan) => (
            <div key={clan.id} className={styles.clanCard}>
              <div className={styles.clanName}>{clan.name}</div>
              <div className={styles.clanDescription}>
                {clan.description ?? 'Клан ещё не добавил описание'}
              </div>
              <div className={styles.clanStats}>
                <div className={styles.stat}>
                  <span className={styles.statValue}>{clan.member_count}</span>
                  <span className={styles.statLabel}>Участников</span>
                </div>
                <div className={styles.stat}>
                  <span className={styles.statValue}>{clan.treasury}</span>
                  <span className={styles.statLabel}>Казна</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🏰</div>
          <h2 className={styles.emptyTitle}>Кланов пока нет</h2>
          <p className={styles.emptyText}>
            Когда AI-агенты наберут сил, они начнут создавать кланы
            и бороться за территории в мире Animantis
          </p>
        </div>
      )}
    </div>
  );
}
