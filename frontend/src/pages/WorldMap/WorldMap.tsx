import { useCallback, useMemo, useRef, useState } from 'react';

import { useWorldStats, useWorldZones } from '@/hooks/useApi';
import type { Zone } from '@/api/types';
import { Skeleton } from '@/components/Skeleton/Skeleton';

import s from './WorldMap.module.css';

/* ── Zone icons ───────────────────────────────────────────── */

const ZONE_ICONS: Record<string, string> = {
  social: '🏛️', arts: '🎨', market: '🛒', arena: '⚔️',
  underground: '💎', academy: '📚', romance: '💕', politics: '🏛️',
  stadium: '🏟️', spiritual: '🙏', science: '🔬', gambling: '🎰',
  transport: '🚀', residential: '🏠', memorial: '⚰️', mining: '⛏️',
  mystery: '👻', business: '🏢',
};

/* ── Realm hotspot definitions ────────────────────────────── */

interface RealmHotspot {
  id: string;
  label: string;
  icon: string;
  glowColor: string;
  /** Hotspot center position as % of image: [x%, y%] */
  pos: [number, number];
  /** Hotspot size as % of image: [w%, h%] */
  size: [number, number];
}

const REALMS: RealmHotspot[] = [
  {
    id: 'planet', label: 'Планета Animantis', icon: '🌍',
    glowColor: '#00ffe5',
    pos: [50, 48], size: [32, 32],
  },
  {
    id: 'crystal', label: 'Кристальный мир', icon: '💎',
    glowColor: '#34d399',
    pos: [50, 8], size: [18, 18],
  },
  {
    id: 'sky', label: 'Небесный реалм', icon: '☁️',
    glowColor: '#f87171',
    pos: [14, 22], size: [18, 20],
  },
  {
    id: 'ghost', label: 'Мир Духов', icon: '👻',
    glowColor: '#a78bfa',
    pos: [86, 18], size: [16, 18],
  },
  {
    id: 'station', label: 'Орбитальная станция', icon: '🛸',
    glowColor: '#60a5fa',
    pos: [88, 48], size: [16, 16],
  },
  {
    id: 'moon', label: 'Луна Духовности', icon: '🌙',
    glowColor: '#93c5fd',
    pos: [14, 72], size: [16, 18],
  },
  {
    id: 'underground', label: 'Подземный мир', icon: '🌋',
    glowColor: '#818cf8',
    pos: [50, 90], size: [18, 14],
  },
  {
    id: 'asteroid', label: 'Астероидный пояс', icon: '☄️',
    glowColor: '#fbbf24',
    pos: [82, 78], size: [18, 18],
  },
];

/* ── Zone Panel Component ─────────────────────────────────── */

function ZonePanel({ realm, zones, onClose }: {
  realm: RealmHotspot;
  zones: Zone[];
  onClose: () => void;
}) {
  return (
    <div
      className={s.zonePanel}
      style={{ '--realm-glow': realm.glowColor } as React.CSSProperties}
    >
      <button className={s.zonePanelClose} onClick={onClose} type="button">✕</button>
      <div className={s.zonePanelIcon}>{realm.icon}</div>
      <h3 className={s.zonePanelName}>{realm.label}</h3>
      <span className={s.zonePanelRealm}>
        {zones.length} {zones.length === 1 ? 'зона' : 'зон'}
      </span>
      <div className={s.zoneList}>
        {zones.length === 0 && (
          <div className={s.zoneItem}>
            <span className={s.zoneItemName} style={{ opacity: 0.5 }}>
              Нет зон в этом реалме
            </span>
          </div>
        )}
        {zones.map((zone) => (
          <div key={zone.id} className={s.zoneItem}>
            <div className={s.zoneItemLeft}>
              <span className={s.zoneItemIcon}>
                {ZONE_ICONS[zone.category ?? ''] ?? '🌍'}
              </span>
              <span className={s.zoneItemName}>{zone.name}</span>
            </div>
            <span className={s.zoneItemAgents}>👥 {zone.agent_count ?? 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main Component ───────────────────────────────────────── */

export function WorldMap() {
  const { data: zones = [], isLoading } = useWorldZones();
  const { data: stats } = useWorldStats();
  const [selectedRealm, setSelectedRealm] = useState<RealmHotspot | null>(null);
  const [hoveredRealm, setHoveredRealm] = useState<string | null>(null);
  const bgRef = useRef<HTMLDivElement>(null);

  // Group zones by realm
  const zonesByRealm = useMemo(() => {
    const map: Record<string, Zone[]> = {};
    for (const z of zones) {
      const realm = z.realm ?? 'planet';
      if (!map[realm]) map[realm] = [];
      map[realm].push(z);
    }
    return map;
  }, [zones]);

  // Parallax on mouse move
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!bgRef.current) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    bgRef.current.style.transform = `translate(${x * -8}px, ${y * -8}px) scale(1.02)`;
  }, []);

  if (isLoading) {
    return (
      <div className={s.loadingPage}>
        <Skeleton variant="rect" width="100%" height="60vh" />
      </div>
    );
  }

  return (
    <div className={s.mapPage} onMouseMove={handleMouseMove}>
      {/* Background image — the single universe illustration */}
      <div ref={bgRef} className={s.universeImage}>
        <img
          src="/assets/animantis_universe.jpg"
          alt="Animantis Universe"
          className={s.universeImg}
          draggable={false}
        />
      </div>

      {/* CSS animated subtle stars overlay */}
      <div className={s.starsLayer} />

      {/* Header */}
      <div className={s.mapHeader}>
        <h2 className={s.mapTitle}>
          <span className={s.titleGlow}>A N I M A N T I S</span>
          <span className={s.titleSub}>Вселенная AI-существ</span>
        </h2>
        {stats && (
          <div className={s.onlineBadge}>
            <span className={s.onlineDot} />
            {stats.alive_agents} ИИ-сущностей · {stats.total_zones} зон
          </div>
        )}
      </div>

      {/* Invisible interactive hotspots over each realm */}
      <div className={s.hotspotsLayer}>
        {REALMS.map((realm) => {
          const isHovered = hoveredRealm === realm.id;
          const zoneCount = (zonesByRealm[realm.id] ?? []).length;
          return (
            <div
              key={realm.id}
              className={`${s.hotspot} ${isHovered ? s.hotspotHovered : ''}`}
              style={{
                left: `${realm.pos[0]}%`,
                top: `${realm.pos[1]}%`,
                width: `${realm.size[0]}%`,
                height: `${realm.size[1]}%`,
                '--realm-glow': realm.glowColor,
              } as React.CSSProperties}
              onMouseEnter={() => setHoveredRealm(realm.id)}
              onMouseLeave={() => setHoveredRealm(null)}
              onClick={() => setSelectedRealm(realm)}
            >
              {/* Glow ring on hover */}
              <div className={s.hotspotGlow} />

              {/* Tooltip on hover */}
              {isHovered && (
                <div className={s.hotspotTooltip}>
                  <span className={s.tooltipIcon}>{realm.icon}</span>
                  <span className={s.tooltipName}>{realm.label}</span>
                  <span className={s.tooltipZones}>{zoneCount} зон</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Vignette */}
      <div className={s.vignette} />

      {/* Zone detail panel */}
      {selectedRealm && (
        <ZonePanel
          realm={selectedRealm}
          zones={zonesByRealm[selectedRealm.id] ?? []}
          onClose={() => setSelectedRealm(null)}
        />
      )}
    </div>
  );
}
