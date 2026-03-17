import { Suspense, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html, Sphere, useTexture, Ring, Sparkles } from '@react-three/drei';

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

const REALM_CONFIG: Record<string, {
  color: string;
  label: string;
  icon: string;
  orbitRadius: number;
  orbitSpeed: number;
  size: number;
  glowIntensity: number;
  texture: string;
}> = {
  planet: {
    color: '#00ffe5', label: 'Планета Animantis', icon: '🌍',
    orbitRadius: 0, orbitSpeed: 0, size: 5, glowIntensity: 2.5,
    texture: '/assets/planet_animantis.jpg',
  },
  moon: {
    color: '#c4b5fd', label: 'Луна Духовности', icon: '🌙',
    orbitRadius: 18, orbitSpeed: 0.06, size: 2.5, glowIntensity: 1.5,
    texture: '/assets/planet_moon.jpg',
  },
  station: {
    color: '#60a5fa', label: 'Орбитальная станция', icon: '🛸',
    orbitRadius: 26, orbitSpeed: 0.1, size: 2.0, glowIntensity: 2.0,
    texture: '/assets/planet_station.jpg',
  },
  asteroid: {
    color: '#fbbf24', label: 'Астероидный пояс', icon: '☄️',
    orbitRadius: 34, orbitSpeed: 0.04, size: 1.8, glowIntensity: 1.2,
    texture: '/assets/planet_asteroid.jpg',
  },
  ghost: {
    color: '#a78bfa', label: 'Призрачное измерение', icon: '👻',
    orbitRadius: 42, orbitSpeed: 0.025, size: 2.2, glowIntensity: 1.8,
    texture: '/assets/planet_ghost.jpg',
  },
};

/* ── Custom shader materials ─────────────────────────────────── */

const atmosphereVertexShader = `
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vNormal = normalize(normalMatrix * normal);
    vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const atmosphereFragmentShader = `
  uniform vec3 glowColor;
  uniform float intensity;
  uniform float power;
  varying vec3 vNormal;
  varying vec3 vPosition;
  void main() {
    vec3 viewDir = normalize(-vPosition);
    float fresnel = 1.0 - dot(viewDir, vNormal);
    fresnel = pow(fresnel, power) * intensity;
    gl_FragColor = vec4(glowColor, fresnel * 0.7);
  }
`;

/* ── Atmosphere Glow Component ───────────────────────────────── */

function AtmosphereGlow({ radius, color, intensity = 1.5, power = 3.0 }: {
  radius: number;
  color: string;
  intensity?: number;
  power?: number;
}) {
  const uniforms = useMemo(() => ({
    glowColor: { value: new THREE.Color(color) },
    intensity: { value: intensity },
    power: { value: power },
  }), [color, intensity, power]);

  return (
    <Sphere args={[radius, 64, 64]}>
      <shaderMaterial
        vertexShader={atmosphereVertexShader}
        fragmentShader={atmosphereFragmentShader}
        uniforms={uniforms}
        transparent
        side={THREE.BackSide}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Sphere>
  );
}

/* ── Planet Animantis (center) ──────────────────────────────── */

function CentralPlanet({ zones, onSelectZone }: { zones: Zone[]; onSelectZone: (z: Zone) => void }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  const textures = useTexture({ map: REALM_CONFIG.planet.texture });

  useFrame((state) => {
    if (meshRef.current) meshRef.current.rotation.y += 0.0008;
    if (ringRef.current) ringRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.2) * 0.05;
  });

  const planetZones = zones.filter((z) => z.realm === 'planet');

  return (
    <group>
      {/* Planet body — emissive for bloom */}
      <Sphere ref={meshRef} args={[5, 64, 64]}>
        <meshStandardMaterial
          map={textures.map}
          emissive="#00ffe5"
          emissiveIntensity={0.6}
          roughness={0.6}
          metalness={0.2}
          toneMapped={false}
        />
      </Sphere>

      {/* Atmosphere glow layers */}
      <AtmosphereGlow radius={5.6} color="#00ffe5" intensity={2.5} power={2.5} />
      <AtmosphereGlow radius={6.2} color="#00ffe5" intensity={0.8} power={4.0} />
      <AtmosphereGlow radius={7.0} color="#7b2fff" intensity={0.3} power={5.0} />

      {/* Planet rings */}
      <Ring ref={ringRef} args={[7, 9.5, 128]} rotation={[Math.PI / 2.2, 0, 0]}>
        <meshBasicMaterial
          color="#7b2fff"
          transparent
          opacity={0.06}
          side={THREE.DoubleSide}
          toneMapped={false}
        />
      </Ring>
      <Ring args={[9.8, 10.5, 128]} rotation={[Math.PI / 2.5, 0.1, 0]}>
        <meshBasicMaterial
          color="#00ffe5"
          transparent
          opacity={0.03}
          side={THREE.DoubleSide}
          toneMapped={false}
        />
      </Ring>

      {/* Core light */}
      <pointLight color="#00ffe5" intensity={200} distance={80} decay={2} />

      {/* Sparkle particles around planet */}
      <Sparkles
        count={100}
        scale={12}
        size={1.5}
        speed={0.3}
        color="#00ffe5"
        opacity={0.4}
      />

      {/* Zone markers on planet surface */}
      {planetZones.map((zone) => {
        const phi = ((zone.y ?? 0) + 4) / 8 * Math.PI;
        const theta = ((zone.x ?? 0) + 4) / 8 * Math.PI * 2;
        const r = 5.5;
        const x = r * Math.sin(phi) * Math.cos(theta);
        const y = r * Math.cos(phi);
        const z = r * Math.sin(phi) * Math.sin(theta);

        return (
          <group key={zone.id} position={[x, y, z]}>
            {/* Glowing beacon */}
            <mesh>
              <sphereGeometry args={[0.12, 8, 8]} />
              <meshBasicMaterial color="#00ffe5" toneMapped={false} />
            </mesh>
            {/* Beacon glow */}
            <pointLight color="#00ffe5" intensity={2} distance={2} decay={2} />
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

/* ── Energy Connection Line ──────────────────────────────────── */

function EnergyConnection({ from, to, color }: {
  from: THREE.Vector3;
  to: THREE.Vector3;
  color: string;
}) {
  const lineRef = useRef<THREE.Line>(null);
  const points = useMemo(() => {
    const mid = new THREE.Vector3().lerpVectors(from, to, 0.5);
    mid.y += 3;
    const curve = new THREE.QuadraticBezierCurve3(from, mid, to);
    return curve.getPoints(50);
  }, [from, to]);

  const lineObj = useMemo(() => {
    const geo = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineBasicMaterial({
      color,
      transparent: true,
      opacity: 0.2,
      blending: THREE.AdditiveBlending,
    });
    mat.toneMapped = false;
    return new THREE.Line(geo, mat);
  }, [points, color]);

  useFrame((state) => {
    if (lineObj) {
      const mat = lineObj.material as THREE.LineBasicMaterial;
      mat.opacity = 0.15 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  return <primitive ref={lineRef} object={lineObj} />;
}

/* ── Orbiting Realm ─────────────────────────────────────────── */

function OrbitingRealm({ realm, zones, onSelectZone }: {
  realm: string;
  zones: Zone[];
  onSelectZone: (z: Zone) => void;
}) {
  const groupRef = useRef<THREE.Group>(null);
  const meshRef = useRef<THREE.Mesh>(null);
  const config = REALM_CONFIG[realm];
  const textures = useTexture({ map: config.texture });
  const [hovered, setHovered] = useState(false);

  useFrame((state) => {
    if (groupRef.current && config) {
      groupRef.current.rotation.y = state.clock.elapsedTime * config.orbitSpeed;
    }
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.003;
    }
  });

  if (!config || config.orbitRadius === 0) return null;

  return (
    <>
      {/* Orbit path ring — glowing */}
      <Ring args={[config.orbitRadius - 0.04, config.orbitRadius + 0.04, 256]} rotation={[Math.PI / 2, 0, 0]}>
        <meshBasicMaterial
          color={config.color}
          transparent
          opacity={0.08}
          side={THREE.DoubleSide}
          toneMapped={false}
          blending={THREE.AdditiveBlending}
        />
      </Ring>

      {/* Orbiting body */}
      <group ref={groupRef}>
        <group position={[config.orbitRadius, 0, 0]}>
          {/* Planet mesh */}
          <Sphere
            ref={meshRef}
            args={[config.size, 48, 48]}
            onPointerOver={() => setHovered(true)}
            onPointerOut={() => setHovered(false)}
            onClick={() => { if (zones[0]) onSelectZone(zones[0]); }}
          >
            <meshStandardMaterial
              map={textures.map}
              emissive={config.color}
              emissiveIntensity={hovered ? 1.0 : 0.5}
              roughness={0.6}
              metalness={0.2}
              toneMapped={false}
            />
          </Sphere>

          {/* Atmosphere layers */}
          <AtmosphereGlow
            radius={config.size * 1.15}
            color={config.color}
            intensity={hovered ? config.glowIntensity * 2 : config.glowIntensity}
            power={3.0}
          />
          <AtmosphereGlow
            radius={config.size * 1.3}
            color={config.color}
            intensity={hovered ? 0.6 : 0.2}
            power={5.0}
          />

          {/* Hover light burst */}
          {hovered && (
            <pointLight color={config.color} intensity={30} distance={15} decay={2} />
          )}

          {/* Sparkles */}
          <Sparkles
            count={30}
            scale={config.size * 3}
            size={0.8}
            speed={0.2}
            color={config.color}
            opacity={0.3}
          />

          {/* Label */}
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

/* ── Nebula Background ───────────────────────────────────────── */

function NebulaBackground() {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.z = state.clock.elapsedTime * 0.003;
    }
  });

  return (
    <group>
      {/* Deep space lights creating nebula effect */}
      <pointLight position={[80, 50, -80]} color="#7b2fff" intensity={15} distance={250} decay={2} />
      <pointLight position={[-100, -30, 60]} color="#00ffe5" intensity={10} distance={200} decay={2} />
      <pointLight position={[60, -60, -40]} color="#ff2d7b" intensity={8} distance={180} decay={2} />
      <pointLight position={[-40, 80, 80]} color="#4f46e5" intensity={6} distance={200} decay={2} />

      {/* Large ambient nebula spheres */}
      <Sphere ref={ref} args={[150, 32, 32]} position={[60, 20, -80]}>
        <meshBasicMaterial
          color="#7b2fff"
          transparent
          opacity={0.015}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>
      <Sphere args={[120, 32, 32]} position={[-50, -30, 60]}>
        <meshBasicMaterial
          color="#00ffe5"
          transparent
          opacity={0.01}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>
      <Sphere args={[100, 32, 32]} position={[30, -50, -40]}>
        <meshBasicMaterial
          color="#ff2d7b"
          transparent
          opacity={0.008}
          side={THREE.BackSide}
          blending={THREE.AdditiveBlending}
        />
      </Sphere>
    </group>
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

  const orbitingRealms = Object.keys(REALM_CONFIG).filter((k) => k !== 'planet');

  // Energy connection endpoints
  const connectionTargets = useMemo(() => {
    return orbitingRealms.map((realm) => ({
      realm,
      target: new THREE.Vector3(REALM_CONFIG[realm].orbitRadius, 0, 0),
      color: REALM_CONFIG[realm].color,
    }));
  }, []);

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={1.5} />
      <directionalLight position={[30, 20, 40]} intensity={2.0} color="#ffffff" />
      <directionalLight position={[-20, -10, -30]} intensity={0.5} color="#7b2fff" />

      {/* Stars — dense and multi-layered */}
      <Stars radius={300} depth={100} count={12000} factor={6} saturation={0.3} fade speed={0.5} />
      <Stars radius={200} depth={50} count={4000} factor={3} saturation={0.6} fade speed={0.8} />

      {/* Nebula background */}
      <NebulaBackground />

      {/* Central Planet */}
      <CentralPlanet zones={zones} onSelectZone={onSelectZone} />

      {/* Energy connections from center to each realm */}
      {connectionTargets.map(({ realm, target, color }) => (
        <EnergyConnection
          key={realm}
          from={new THREE.Vector3(0, 0, 0)}
          to={target}
          color={color}
        />
      ))}

      {/* Orbiting Realms */}
      {orbitingRealms.map((realm) => (
        <OrbitingRealm
          key={realm}
          realm={realm}
          zones={zonesByRealm[realm] ?? []}
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
      <div className={s.zonePanelGlow} style={{ background: realmConfig?.color }} />
      <div className={s.zonePanelIcon}>{icon}</div>
      <h3 className={s.zonePanelName}>{zone.name}</h3>
      <span className={s.zonePanelRealm}>
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

      {/* Realm selector */}
      <RealmSelector activeRealm={null} onSelect={setActiveRealm} />

      {/* 3D Canvas */}
      <div className={s.canvasContainer}>
        <Canvas
          camera={{ position: [0, 18, 45], fov: 50 }}
          gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
          dpr={[1, 2]}
        >
          <color attach="background" args={['#020305']} />
          <fog attach="fog" args={['#020305', 80, 200]} />

          <Suspense fallback={null}>
            <UniverseScene zones={zones} onSelectZone={setSelectedZone} />
          </Suspense>

          <OrbitControls
            enablePan
            enableZoom
            enableRotate
            autoRotate
            autoRotateSpeed={0.12}
            minDistance={14}
            maxDistance={100}
            maxPolarAngle={Math.PI / 1.2}
            dampingFactor={0.05}
            enableDamping
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
