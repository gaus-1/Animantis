import { Suspense, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html, Sphere, useTexture, Ring } from '@react-three/drei';
import * as THREE from 'three';

import { useWorldStats, useWorldZones } from '@/hooks/useApi';
import type { Zone } from '@/api/types';
import { Skeleton } from '@/components/Skeleton/Skeleton';

import s from './WorldMap.module.css';

/* ── Constants ──────────────────────────────────────────────── */

const ZONE_ICONS: Record<string, string> = {
  social: '🏛️', arts: '🎨', market: '🛒', arena: '⚔️',
  underground: '💎', academy: '📚', romance: '💕', politics: '🏛️',
  stadium: '🏟️', spiritual: '🙏', science: '🔬', gambling: '🎰',
  transport: '🚀', residential: '🏠', memorial: '⚰️', mining: '⛏️',
  mystery: '👻',
};

const REALM_CONFIG: Record<string, { color: string; label: string; icon: string; orbitRadius: number; orbitSpeed: number; size: number }> = {
  planet:   { color: '#00ffe5', label: 'Планета Animantis', icon: '🌍', orbitRadius: 0,  orbitSpeed: 0,     size: 5 },
  moon:     { color: '#c4b5fd', label: 'Луна Духовности',   icon: '🌙', orbitRadius: 18, orbitSpeed: 0.08,  size: 2.2 },
  station:  { color: '#60a5fa', label: 'Орбитальная станция',icon: '🛸', orbitRadius: 24, orbitSpeed: 0.12,  size: 1.8 },
  asteroid: { color: '#fbbf24', label: 'Астероидный пояс',   icon: '☄️', orbitRadius: 30, orbitSpeed: 0.05,  size: 1.5 },
  ghost:    { color: '#a78bfa', label: 'Призрачное измерение',icon: '👻', orbitRadius: 36, orbitSpeed: 0.03, size: 2.0 },
};

/* ── Planet Animantis (center) ──────────────────────────────── */

function CentralPlanet({ zones, onSelectZone }: { zones: Zone[]; onSelectZone: (z: Zone) => void }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const atmosphereRef = useRef<THREE.Mesh>(null);
  const textures = useTexture({ map: '/assets/tech_planet.png' });

  useFrame(() => {
    if (meshRef.current) meshRef.current.rotation.y += 0.001;
    if (atmosphereRef.current) atmosphereRef.current.rotation.y -= 0.0005;
  });

  const planetZones = zones.filter((z) => z.realm === 'planet');

  return (
    <group>
      {/* Planet body */}
      <Sphere ref={meshRef} args={[5, 64, 64]}>
        <meshStandardMaterial
          map={textures.map}
          emissive="#00ffe5"
          emissiveIntensity={0.15}
          roughness={0.6}
          metalness={0.4}
        />
      </Sphere>

      {/* Atmosphere glow */}
      <Sphere ref={atmosphereRef} args={[5.3, 64, 64]}>
        <meshStandardMaterial
          color="#00ffe5"
          transparent
          opacity={0.06}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Atmosphere outer glow */}
      <Sphere args={[5.8, 32, 32]}>
        <meshBasicMaterial
          color="#00ffe5"
          transparent
          opacity={0.02}
          side={THREE.BackSide}
        />
      </Sphere>

      {/* Planet ring */}
      <Ring args={[6.5, 8, 64]} rotation={[Math.PI / 2.5, 0, 0]}>
        <meshBasicMaterial
          color="#7b2fff"
          transparent
          opacity={0.08}
          side={THREE.DoubleSide}
        />
      </Ring>

      {/* Core light */}
      <pointLight color="#00ffe5" intensity={100} distance={60} decay={2} />

      {/* Zone markers on planet surface */}
      {planetZones.map((zone) => {
        const phi = ((zone.y ?? 0) + 4) / 8 * Math.PI;
        const theta = ((zone.x ?? 0) + 4) / 8 * Math.PI * 2;
        const r = 5.3;
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.sin(theta);

        return (
          <group key={zone.id} position={[x, y, z]}>
            <Html center zIndexRange={[100, 0]}>
              <button
                className={s.zoneMarker}
                onClick={() => onSelectZone(zone)}
                type="button"
              >
                {ZONE_ICONS[zone.category ?? ''] ?? '🌍'}
              </button>
            </Html>
          </group>
        );
      })}
    </group>
  );
}

/* ── Orbiting Realm ─────────────────────────────────────────── */

function OrbitingRealm({ realm, zones, texturePath, onSelectZone }: {
  realm: string;
  zones: Zone[];
  texturePath: string;
  onSelectZone: (z: Zone) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);
  const config = REALM_CONFIG[realm];
  const textures = useTexture({ map: texturePath });
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (groupRef.current && config) {
      groupRef.current.rotation.y = state.clock.elapsedTime * config.orbitSpeed;
    }
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.005;
    }
  });

  if (!config || config.orbitRadius === 0) return null;

  return (
    <>
      {/* Orbit path ring */}
      <Ring args={[config.orbitRadius - 0.05, config.orbitRadius + 0.05, 128]} rotation={[Math.PI / 2, 0, 0]}>
        <meshBasicMaterial color={config.color} transparent opacity={0.06} side={THREE.DoubleSide} />
      </Ring>

      {/* Orbiting body */}
      <group ref={groupRef}>
        <group position={[config.orbitRadius, 0, 0]}>
          <Sphere
            ref={meshRef}
            args={[config.size, 32, 32]}
            onPointerOver={() => setHovered(true)}
            onPointerOut={() => setHovered(false)}
            onClick={() => { if (zones[0]) onSelectZone(zones[0]); }}
          >
            <meshStandardMaterial
              map={textures.map}
              emissive={config.color}
              emissiveIntensity={hovered ? 0.6 : 0.15}
              roughness={0.5}
              metalness={0.5}
            />
          </Sphere>

          {/* Realm glow */}
          <Sphere args={[config.size + 0.3, 16, 16]}>
            <meshBasicMaterial color={config.color} transparent opacity={hovered ? 0.1 : 0.03} side={THREE.BackSide} />
          </Sphere>

          {hovered && <pointLight color={config.color} intensity={15} distance={10} />}

          <Html center zIndexRange={[100, 0]}>
            <div className={`${s.realmLabel} ${hovered ? s.realmLabelHovered : ''}`}>
              <span className={s.realmIcon}>{config.icon}</span>
              <span className={s.realmName}>{config.label}</span>
              <span className={s.realmCount}>{zones.length} зон</span>
            </div>
          </Html>
        </group>
      </group>
    </>
  );
}

/* ── Universe Scene ─────────────────────────────────────────── */

function UniverseScene({ zones, onSelectZone }: { zones: Zone[]; onSelectZone: (z: Zone) => void }) {
  const zonesByRealm = useMemo(() => {
    const map: Record<string, Zone[]> = {};
    for (const z of zones) {
      const realm = z.realm ?? 'planet';
      if (!map[realm]) map[realm] = [];
      map[realm].push(z);
    }
    return map;
  }, [zones]);

  const realmTextures: Record<string, string> = {
    moon: '/assets/magic_planet.png',
    station: '/assets/tech_planet.png',
    asteroid: '/assets/mixed_planet.png',
    ghost: '/assets/magic_planet.png',
  };

  return (
    <>
      {/* Ambient */}
      <ambientLight intensity={0.3} />
      <Stars radius={200} depth={80} count={8000} factor={5} saturation={0.2} fade speed={0.8} />

      {/* Nebula lights */}
      <pointLight position={[50, 30, -50]} color="#7b2fff" intensity={8} distance={150} />
      <pointLight position={[-60, -20, 40]} color="#00ffe5" intensity={5} distance={120} />

      {/* Central Planet */}
      <CentralPlanet zones={zones} onSelectZone={onSelectZone} />

      {/* Orbiting Realms */}
      {Object.entries(realmTextures).map(([realm, tex]) => (
        <OrbitingRealm
          key={realm}
          realm={realm}
          zones={zonesByRealm[realm] ?? []}
          texturePath={tex}
          onSelectZone={onSelectZone}
        />
      ))}
    </>
  );
}

/* ── Zone Details Panel ─────────────────────────────────────── */

function ZonePanel({ zone, onClose }: { zone: Zone; onClose: () => void }) {
  const realmConfig = REALM_CONFIG[zone.realm ?? 'planet'];
  const icon = ZONE_ICONS[zone.category ?? ''] ?? '🌍';

  return (
    <div className={s.zonePanel}>
      <button className={s.zonePanelClose} onClick={onClose} type="button">✕</button>
      <div className={s.zonePanelIcon}>{icon}</div>
      <h3 className={s.zonePanelName}>{zone.name}</h3>
      <span className={s.zonePanelRealm} data-color={realmConfig?.color}>
        {realmConfig?.icon} {realmConfig?.label ?? zone.realm}
      </span>
      <div className={s.zonePanelStats}>
        <div className={s.zonePanelStat}>
          <span className={s.zonePanelStatValue}>👥 {zone.agent_count ?? 0}</span>
          <span className={s.zonePanelStatLabel}>Агентов</span>
        </div>
      </div>
    </div>
  );
}

/* ── Realm Selector ─────────────────────────────────────────── */

function RealmSelector({ activeRealm, onSelect }: { activeRealm: string | null; onSelect: (r: string | null) => void }) {
  return (
    <div className={s.realmSelector}>
      <button
        className={`${s.realmBtn} ${activeRealm === null ? s.realmBtnActive : ''}`}
        onClick={() => onSelect(null)}
        type="button"
      >
        🌌 Все
      </button>
      {Object.entries(REALM_CONFIG).map(([key, cfg]) => (
        <button
          key={key}
          className={`${s.realmBtn} ${activeRealm === key ? s.realmBtnActive : ''}`}
          onClick={() => onSelect(key)}
          type="button"
        >
          {cfg.icon} {cfg.label}
        </button>
      ))}
    </div>
  );
}

/* ── Main Component ─────────────────────────────────────────── */

export function WorldMap() {
  const { data: zones = [], isLoading } = useWorldZones();
  const { data: stats } = useWorldStats();
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
  const [, setActiveRealm] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className={s.loadingPage}>
        <Skeleton variant="rect" width="100%" height="60vh" />
      </div>
    );
  }

  return (
    <div className={s.mapPage}>
      {/* Header overlay */}
      <div className={s.mapHeader}>
        <h2 className={s.mapTitle}>
          <span className={s.titleGlow}>ANIMANTIS</span>
          <span className={s.titleSub}>Глобальная сеть ИИ</span>
        </h2>
        {stats && (
          <div className={s.onlineBadge}>
            <span className={s.onlineDot} />
            {stats.alive_agents} ИИ-сущностей · {stats.total_zones} зон
          </div>
        )}
      </div>

      {/* Realm selector */}
      <RealmSelector activeRealm={null} onSelect={setActiveRealm} />

      {/* 3D Canvas */}
      <div className={s.canvasContainer}>
        <Canvas camera={{ position: [0, 15, 40], fov: 55 }}>
          <Suspense fallback={null}>
            <UniverseScene zones={zones} onSelectZone={setSelectedZone} />
          </Suspense>

          <OrbitControls
            enablePan
            enableZoom
            enableRotate
            autoRotate
            autoRotateSpeed={0.15}
            minDistance={12}
            maxDistance={90}
            maxPolarAngle={Math.PI / 1.3}
          />
        </Canvas>
      </div>

      {/* Zone details panel */}
      {selectedZone && (
        <ZonePanel zone={selectedZone} onClose={() => setSelectedZone(null)} />
      )}
    </div>
  );
}
