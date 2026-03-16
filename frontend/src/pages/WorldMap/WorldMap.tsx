import { Suspense, useMemo, useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Html, Sphere, useTexture } from '@react-three/drei';
import * as THREE from 'three';

import { useWorldStats, useWorldZones } from '@/hooks/useApi';
import type { Zone } from '@/api/types';

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

// Colors based on realm
const REALM_COLORS: Record<string, string> = {
  'AGENTS': '#00ffe5', // Cyan
  'HUMANS': '#7b2fff', // Purple
  'MIXED': '#ff2d78', // Pink
};

function ZoneNode({ zone, position, textures }: { zone: Zone; position: [number, number, number]; textures: any }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Create an animated glow effect
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.005;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2 + position[0]) * 0.5;
    }
  });

  const baseColor = REALM_COLORS[zone.realm] || '#00ffe5';
  const icon = ZONE_ICONS[zone.name] ?? '🌍';
  const agentCount = zone.agent_count ?? 0;

  // Select texture based on realm
  let mapTexture = textures.tech;
  if (zone.realm === 'HUMANS') mapTexture = textures.magic;
  if (zone.realm === 'MIXED') mapTexture = textures.mixed;

  return (
    <group position={position}>
      <Sphere
        ref={meshRef}
        args={[hovered ? 1.8 : 1.5, 64, 64]}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          map={mapTexture}
          emissive={baseColor}
          emissiveIntensity={hovered ? 0.8 : 0.2}
          emissiveMap={mapTexture}
          roughness={0.4}
          metalness={0.6}
        />
      </Sphere>

      {hovered && (
        <pointLight color={baseColor} intensity={20} distance={10} />
      )}

      <Html center zIndexRange={[100, 0]}>
        <div className={`${s.nodeLabel} ${hovered ? s.nodeLabelHovered : ''}`}>
          <div className={s.nodeIcon}>{icon}</div>
          <div className={s.nodeInfo}>
            <div className={s.nodeName}>{zone.name}</div>
            <div className={s.nodeRealm}>{zone.realm}</div>
            <div className={s.nodeAgents}>
              👥 {agentCount} агентов
            </div>
          </div>
        </div>
      </Html>
    </group>
  );
}

function UniverseScene({ zones }: { zones: Zone[] }) {
  // Load textures
  const textures = useTexture({
    bg: '/assets/space_bg.png',
    tech: '/assets/tech_planet.png',
    magic: '/assets/magic_planet.png',
    mixed: '/assets/mixed_planet.png',
  });

  textures.bg.mapping = THREE.EquirectangularReflectionMapping;
  textures.tech.mapping = THREE.EquirectangularReflectionMapping;
  textures.magic.mapping = THREE.EquirectangularReflectionMapping;
  textures.mixed.mapping = THREE.EquirectangularReflectionMapping;

  // Distribute nodes in a spiral or cluster around the center
  const nodes = useMemo(() => {
    const items = [];
    const count = zones.length || 12; // Fallback to 12 if empty
    const goldenRatio = (1 + Math.sqrt(5)) / 2;

    for (let i = 0; i < count; i++) {
      // Fibonacci sphere distribution for an organic cluster
      const theta = 2 * Math.PI * i / goldenRatio;
      const phi = Math.acos(1 - 2 * (i + 0.5) / count);

      const radius = 20; // Spread distance

      const x = Math.cos(theta) * Math.sin(phi) * radius;
      const y = Math.cos(phi) * radius * 0.4; // Flatten the Y axis slightly
      const z = Math.sin(theta) * Math.sin(phi) * radius;

      items.push({
        zone: zones[i] || { id: i, name: `Сектор ${i}`, realm: 'AGENTS', agent_count: 0 },
        position: [x, y, z] as [number, number, number]
      });
    }
    return items;
  }, [zones]);

  // Central core
  const coreRef = useRef<THREE.Mesh>(null);
  useFrame(() => {
    if (coreRef.current) {
      coreRef.current.rotation.y -= 0.002;
      coreRef.current.rotation.x += 0.001;
    }
  });

  return (
    <>
      <primitive object={new THREE.Scene()} background={textures.bg} attach="background" />

      <group>
        {/* Central Core - The Server / The Anima */}
        <Sphere ref={coreRef} args={[4, 64, 64]} position={[0, 0, 0]}>
          <meshStandardMaterial
            color="#ffffff"
            emissive="#7b2fff"
            emissiveIntensity={2}
            wireframe={true}
          />
        </Sphere>

        {/* Inner Core Light */}
        <pointLight color="#7b2fff" intensity={500} distance={100} decay={2} />

        {/* Nodes */}
        {nodes.map((n) => (
          <ZoneNode key={n.zone.id} zone={n.zone} position={n.position} textures={textures} />
        ))}

        {/* Connecting lines from core to nodes */}
        {nodes.map((n, i) => {
          const points = [
            new THREE.Vector3(0, 0, 0),
            new THREE.Vector3(...n.position)
          ];
          const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
          return (
            <line key={`line-${i}`}>
              <primitive object={lineGeometry} />
              <lineBasicMaterial color={REALM_COLORS[n.zone.realm] || '#00ffe5'} transparent opacity={0.15} />
            </line>
          );
        })}
      </group>
    </>
  );
}

export function WorldMap() {
  const { data: zones = [], isLoading } = useWorldZones();
  const { data: stats } = useWorldStats();

  if (isLoading) return <div className={s.loading}>⏳ Синхронизация с серверами Animantis...</div>;

  return (
    <div className={s.mapPage}>
      <div className={s.mapHeader}>
        <h2 className={s.mapTitle}>Глобальная сеть ИИ</h2>
        {stats && (
          <div className={s.onlineBadge}>
            <span className={s.onlineDot} />
            {stats.alive_agents} ИИ-сущностей
          </div>
        )}
      </div>

      <div className={s.canvasContainer}>
        <Canvas camera={{ position: [0, 20, 35], fov: 60 }}>
          <ambientLight intensity={0.4} />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />

          <Suspense fallback={null}>
            <UniverseScene zones={zones} />
          </Suspense>

          <OrbitControls
            enablePan={true}
            enableZoom={true}
            enableRotate={true}
            autoRotate={true}
            autoRotateSpeed={0.3}
            minDistance={10}
            maxDistance={80}
            maxPolarAngle={Math.PI / 1.5}
          />
        </Canvas>
      </div>
    </div>
  );
}
