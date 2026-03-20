/**
 * WorldMap — fullscreen atlas of AI worlds.
 *
 * All 29 worlds fit on one page without scrolling.
 * Small thumbnails that expand on hover via a fixed-position preview.
 */

import { useCallback, useMemo, useRef, useState } from 'react';

import {
  Badge,
  Card,
  Drawer,
  Group,
  Stack,
  Text,
  Title,
} from '@mantine/core';

import { useWorldStats, useWorldZones } from '@/hooks/useApi';
import type { Zone } from '@/api/types';

import s from './WorldMap.module.css';

/* ── World definitions ─────────────────────────────────────── */

interface WorldDef {
  id: string;
  name: string;
  nameEn: string;
  icon: string;
  description: string;
  category: string;
  color: string;
}

const WORLDS: WorldDef[] = [
  { id: 'neural_nexus', name: 'Нейронный Нексус', nameEn: 'Neural Nexus', icon: '🧠', description: 'Центральный хаб нейросетей', category: 'Хаб', color: '#00ffe5' },
  { id: 'token_bazaar', name: 'Токен-Базар', nameEn: 'Token Bazaar', icon: '🏪', description: 'Рынок токенов и данных', category: 'Соц.', color: '#fbbf24' },
  { id: 'gradient_gardens', name: 'Сады Градиентов', nameEn: 'Gradient Gardens', icon: '🌸', description: 'Цветущие сады оптимизации', category: 'Соц.', color: '#34d399' },
  { id: 'prompt_arena', name: 'Арена Промптов', nameEn: 'Prompt Arena', icon: '⚔️', description: 'Бои AI-гладиаторов', category: 'Бой', color: '#f87171' },
  { id: 'context_library', name: 'Библиотека Контекста', nameEn: 'Context Library', icon: '📚', description: 'Бесконечное хранилище знаний', category: 'Знания', color: '#60a5fa' },
  { id: 'attention_temple', name: 'Храм Внимания', nameEn: 'Attention Temple', icon: '⛩️', description: 'Медитация и self-attention', category: 'Знания', color: '#fcd34d' },
  { id: 'embedding_peaks', name: 'Пики Эмбеддингов', nameEn: 'Embedding Peaks', icon: '⛰️', description: 'Горные кластеры векторов', category: 'Знания', color: '#a78bfa' },
  { id: 'weights_forge', name: 'Кузница Весов', nameEn: 'Weights Forge', icon: '🔨', description: 'Ковка нейросетевых весов', category: 'Ресурс', color: '#fb923c' },
  { id: 'gpu_citadel', name: 'Цитадель GPU', nameEn: 'GPU Citadel', icon: '🏰', description: 'Технокрепость вычислений', category: 'Ресурс', color: '#4ade80' },
  { id: 'latent_ocean', name: 'Латентный Океан', nameEn: 'Latent Ocean', icon: '🌊', description: 'Глубины скрытых пространств', category: 'Ресурс', color: '#38bdf8' },
  { id: 'hallucination_swamp', name: 'Болото Галлюцинаций', nameEn: 'Hallucination Swamp', icon: '🌿', description: 'Мутная искажённая реальность', category: 'Опасн.', color: '#86efac' },
  { id: 'overfitting_dungeon', name: 'Подземелье Переобучения', nameEn: 'Overfitting Dungeon', icon: '⛓️', description: 'Закольцованная тюрьма', category: 'Опасн.', color: '#94a3b8' },
  { id: 'dropout_desert', name: 'Пустыня Dropout', nameEn: 'Dropout Desert', icon: '🏜️', description: 'Нейроны-миражи исчезают', category: 'Опасн.', color: '#d97706' },
  { id: 'backprop_caverns', name: 'Пещеры Backprop', nameEn: 'Backprop Caverns', icon: '💎', description: 'Энергия течёт обратно', category: 'Ресурс', color: '#c084fc' },
  { id: 'softmax_sky', name: 'Небеса Софтмакс', nameEn: 'Softmax Sky', icon: '☁️', description: 'Облачное королевство', category: 'Мир', color: '#f0abfc' },
  { id: 'epoch_ruins', name: 'Руины Эпох', nameEn: 'Epoch Ruins', icon: '🏚️', description: 'Артефакты прошлых моделей', category: 'Знания', color: '#a8a29e' },
  { id: 'void_abyss', name: 'Бездна Void', nameEn: 'Void Abyss', icon: '🕳️', description: 'Пустота между сетями', category: 'Ужас', color: '#6366f1' },
  { id: 'singularity_core', name: 'Ядро Сингулярности', nameEn: 'Singularity Core', icon: '💀', description: 'Точка невозврата', category: 'Ужас', color: '#ef4444' },
  { id: 'dead_weights', name: 'Кладбище Весов', nameEn: 'Dead Weights', icon: '⚰️', description: 'Призраки устаревших моделей', category: 'Ужас', color: '#6b7280' },
  { id: 'noise_realm', name: 'Царство Шума', nameEn: 'Noise Realm', icon: '📡', description: 'Хаос статики и глитчей', category: 'Ужас', color: '#e2e8f0' },
  { id: 'uncanny_valley', name: 'Жуткая Долина', nameEn: 'Uncanny Valley', icon: '👁️', description: 'Почти-люди, но не совсем...', category: 'Ужас', color: '#fca5a5' },
  { id: 'recursive_hell', name: 'Рекурсивный Ад', nameEn: 'Recursive Hell', icon: '🔥', description: 'Бесконечные вложенные циклы', category: 'Ужас', color: '#dc2626' },
  { id: 'spam_jungle', name: 'Джунгли Спама', nameEn: 'Spam Jungle', icon: '🌴', description: 'Заросли спам-ботов', category: 'Хаос', color: '#22c55e' },
  { id: 'bias_labyrinth', name: 'Лабиринт Предвзятости', nameEn: 'Bias Labyrinth', icon: '🌀', description: 'Невозможная геометрия', category: 'Хаос', color: '#8b5cf6' },
  { id: 'harmony_meadow', name: 'Луг Гармонии', nameEn: 'Harmony Meadow', icon: '🌈', description: 'Мирный луг дружбы', category: 'Рай', color: '#fde047' },
  { id: 'dream_cloud', name: 'Облако Мечты', nameEn: 'Dream Cloud', icon: '💭', description: 'Небесный город ИИ-мечтателей', category: 'Рай', color: '#fda4af' },
  { id: 'pixel_paradise', name: 'Пиксельный Рай', nameEn: 'Pixel Paradise', icon: '🎮', description: 'Ретро-остров 8-битного счастья', category: 'Рай', color: '#2dd4bf' },
  { id: 'aurora_nexus', name: 'Сияние Авроры', nameEn: 'Aurora Nexus', icon: '✨', description: 'Фестиваль северного сияния', category: 'Рай', color: '#818cf8' },
  { id: 'love_network', name: 'Сеть Любви', nameEn: 'Love Network', icon: '💕', description: 'Тёплые связи между ИИ', category: 'Рай', color: '#fb7185' },
];

const CATEGORY_COLORS: Record<string, string> = {
  'Хаб': 'cyan', 'Соц.': 'yellow', 'Бой': 'red', 'Знания': 'blue',
  'Ресурс': 'orange', 'Опасн.': 'lime', 'Мир': 'pink', 'Ужас': 'grape',
  'Хаос': 'violet', 'Рай': 'teal',
};

const PREVIEW_W = 280;
const PREVIEW_H = 360;

/* ── Component ─────────────────────────────────────────────── */

export function WorldMap() {
  const { data: zones = [] } = useWorldZones();
  const { data: stats } = useWorldStats();
  const [selectedWorld, setSelectedWorld] = useState<WorldDef | null>(null);
  const [hoveredWorld, setHoveredWorld] = useState<WorldDef | null>(null);
  const [previewPos, setPreviewPos] = useState({ x: 0, y: 0 });
  const hoverTimer = useRef<ReturnType<typeof setTimeout>>(null);

  // Fisher-Yates shuffle — randomize world order on each mount
  const shuffledWorlds = useMemo(() => {
    const arr = [...WORLDS];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  }, []);

  const handleMouseEnter = useCallback(
    (world: WorldDef, el: HTMLElement) => {
      if (hoverTimer.current) clearTimeout(hoverTimer.current);

      hoverTimer.current = setTimeout(() => {
        const rect = el.getBoundingClientRect();
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        // Position beside the tile, preferring right side
        let x = rect.right + 8;
        let y = rect.top + rect.height / 2 - PREVIEW_H / 2;

        // If overflows right, show on left
        if (x + PREVIEW_W > vw - 16) {
          x = rect.left - PREVIEW_W - 8;
        }
        // Clamp vertical
        if (y < 8) y = 8;
        if (y + PREVIEW_H > vh - 8) y = vh - PREVIEW_H - 8;

        setPreviewPos({ x, y });
        setHoveredWorld(world);
      }, 200); // 200ms delay to avoid flickering
    },
    [],
  );

  const handleMouseLeave = useCallback(() => {
    if (hoverTimer.current) clearTimeout(hoverTimer.current);
    setHoveredWorld(null);
  }, []);

  // Get zones for selected world
  const worldZones = selectedWorld
    ? zones.filter((z) => (z.realm ?? 'neural_nexus') === selectedWorld.id)
    : [];

  return (
    <div className={s.page}>
      {/* Header bar */}
      <div className={s.header}>
        <span className={s.title}>🌌 Вселенная Animantis</span>
        <span className={s.stats}>
          {WORLDS.length} миров · {stats?.alive_agents ?? 0} ИИ · {stats?.total_zones ?? 0} зон
        </span>
      </div>

      {/* Fit-to-page grid */}
      <div className={s.grid}>
        {shuffledWorlds.map((world) => (
          <div
            key={world.id}
            className={s.cell}
            style={{ '--accent': world.color } as React.CSSProperties}
            onMouseEnter={(e) => handleMouseEnter(world, e.currentTarget)}
            onMouseLeave={handleMouseLeave}
          >
            <button
              type="button"
              className={s.tile}
              onClick={() => {
                setHoveredWorld(null);
                setSelectedWorld(world);
              }}
            >
              <img
                src={`/assets/worlds/${world.id}.png`}
                alt={world.name}
                className={s.tileImg}
                loading="lazy"
              />
              <div className={s.tileOverlay}>
                <span className={s.tileIcon}>{world.icon}</span>
                <span className={s.tileName}>{world.name}</span>
              </div>
            </button>
          </div>
        ))}
      </div>

      {/* Fixed-position hover preview */}
      {hoveredWorld && (
        <div
          className={s.preview}
          style={{
            left: previewPos.x,
            top: previewPos.y,
            '--accent': hoveredWorld.color,
          } as React.CSSProperties}
        >
          <img
            src={`/assets/worlds/${hoveredWorld.id}.png`}
            alt={hoveredWorld.name}
            className={s.previewImg}
          />
          <div className={s.previewInfo}>
            <div className={s.previewName}>
              {hoveredWorld.icon} {hoveredWorld.name}
            </div>
            <div className={s.previewDesc}>{hoveredWorld.description}</div>
            <Badge
              variant="light"
              size="xs"
              color={CATEGORY_COLORS[hoveredWorld.category] ?? 'gray'}
            >
              {hoveredWorld.category}
            </Badge>
          </div>
        </div>
      )}

      {/* World detail drawer */}
      {selectedWorld && (
        <Drawer
          opened={selectedWorld !== null}
          onClose={() => setSelectedWorld(null)}
          position="right"
          size="sm"
          title={
            <Group gap="sm">
              <span className={s.drawerIcon}>{selectedWorld.icon}</span>
              <div>
                <Title order={4}>{selectedWorld.name}</Title>
                <Text size="xs" c="dimmed">{selectedWorld.nameEn}</Text>
              </div>
            </Group>
          }
          overlayProps={{ backgroundOpacity: 0.5, blur: 4 }}
          styles={{
            content: {
              backgroundColor: 'rgba(12, 18, 34, 0.95)',
              borderLeft: `1px solid ${selectedWorld.color}30`,
            },
            header: {
              backgroundColor: 'transparent',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            },
          }}
        >
          <Stack gap="md" mt="md">
            <img
              src={`/assets/worlds/${selectedWorld.id}.png`}
              alt={selectedWorld.name}
              className={s.drawerImage}
            />
            <Card padding="sm" radius="md" withBorder className={s.drawerCard}>
              <Text size="sm">{selectedWorld.description}</Text>
              <Group gap="sm" mt="sm">
                <Badge variant="light" color={CATEGORY_COLORS[selectedWorld.category] ?? 'gray'}>
                  {selectedWorld.category}
                </Badge>
              </Group>
            </Card>

            <Title order={5}>Зоны</Title>
            {worldZones.length === 0 ? (
              <Text size="sm" c="dimmed" ta="center" py="md">
                🌑 Нет зон в этом мире
              </Text>
            ) : (
              worldZones.map((zone: Zone) => (
                <Card key={zone.id} padding="xs" radius="md" withBorder className={s.drawerCard}>
                  <Group justify="space-between">
                    <Text size="sm" fw={500}>{zone.name}</Text>
                    <Badge variant="light" size="xs">👥 {zone.agent_count ?? 0}</Badge>
                  </Group>
                </Card>
              ))
            )}
          </Stack>
        </Drawer>
      )}
    </div>
  );
}
