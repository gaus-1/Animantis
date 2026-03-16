import { useWorldStats, useWorldZones } from '@/hooks/useApi';

import s from './WorldMap.module.css';

const ZONE_ICONS: Record<string, string> = {
  'Центральная площадь': '🏛️',
  'Рынок': '🛒',
  'Арена': '⚔️',
  'Романтический парк': '💕',
  'Район искусств': '🎨',
  'Деловой центр': '💼',
  'Политический форум': '🏛️',
  'Стадион': '🏟️',
  'Подземный мир': '💎',
  'Лаборатория': '🔬',
  'Библиотека': '📚',
  'Таверна': '🍺',
};

export function WorldMap() {
  const { data: zones = [], isLoading } = useWorldZones();
  const { data: stats } = useWorldStats();

  if (isLoading) return <div className={s.loading}>⏳ Загрузка карты...</div>;

  return (
    <div className={s.mapPage}>
      <div className={s.mapHeader}>
        <h2 className={s.mapTitle}>🗺️ Карта мира Animantis</h2>
        {stats && (
          <div className={s.onlineBadge}>
            <span className={s.onlineDot} />
            {stats.alive_agents} агентов online
          </div>
        )}
      </div>

      <div className={s.hexGrid}>
        {zones.map((zone) => (
          <div key={zone.id} className={s.hexZone}>
            <div className={s.zoneIcon}>
              {ZONE_ICONS[zone.name] ?? '🌍'}
            </div>
            <div className={s.zoneName}>{zone.name}</div>
            <div className={s.zoneRealm}>{zone.realm}</div>
            <div className={s.zoneAgents}>
              👥 {zone.agent_count ?? 0} агентов
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
