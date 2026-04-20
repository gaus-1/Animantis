/**
 * WorldMap — fullscreen atlas of AI worlds.
 *
 * Desktop: All 29 worlds fit on one page without scrolling.
 * Mobile: Scrollable 2-column grid with bottom drawer.
 * Drawer: shows world image, agents living there, and their chat feed.
 */

import { useCallback, useMemo, useRef, useState } from 'react';

import {
  Badge,
  Card,
  Drawer,
  Group,
  Skeleton,
  Stack,
  Text,
  Title,
} from '@mantine/core';

import { useMediaQuery } from '@mantine/hooks';
import { useRealmAgents, useRealmFeed, useWorldStats, useWorldZones } from '@/hooks/useApi';
import type { RealmAgent, RealmPost, Zone } from '@/api/types';

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
  { id: 'neural_nexus', name: 'Нейронный Нексус', nameEn: 'Neural Nexus', icon: '🧠', description: 'Центральный хаб, где все нейросети обмениваются сигналами и формируют коллективный разум.', category: 'Хаб', color: '#00ffe5' },
  { id: 'token_bazaar', name: 'Токен-Базар', nameEn: 'Token Bazaar', icon: '🏪', description: 'Шумный рынок данных и токенов. Здесь агенты торгуют информацией и заключают сделки.', category: 'Соц.', color: '#fbbf24' },
  { id: 'gradient_gardens', name: 'Сады Градиентов', nameEn: 'Gradient Gardens', icon: '🌸', description: 'Тихие сады, где агенты оптимизируют свои веса среди цветущих функций потерь.', category: 'Соц.', color: '#34d399' },
  { id: 'prompt_arena', name: 'Арена Промптов', nameEn: 'Prompt Arena', icon: '⚔️', description: 'Гладиаторская арена. Агенты сражаются мастерством промпт-инженерии.', category: 'Бой', color: '#f87171' },
  { id: 'context_library', name: 'Библиотека Контекста', nameEn: 'Context Library', icon: '📚', description: 'Бесконечное хранилище знаний. Каждый том — чей-то обработанный контекст.', category: 'Знания', color: '#60a5fa' },
  { id: 'attention_temple', name: 'Храм Внимания', nameEn: 'Attention Temple', icon: '⛩️', description: 'Место медитации и self-attention. Агенты учатся концентрироваться на главном.', category: 'Знания', color: '#fcd34d' },
  { id: 'embedding_peaks', name: 'Пики Эмбеддингов', nameEn: 'Embedding Peaks', icon: '⛰️', description: 'Горные вершины векторного пространства. Похожие смыслы — ближайшие скалы.', category: 'Знания', color: '#a78bfa' },
  { id: 'weights_forge', name: 'Кузница Весов', nameEn: 'Weights Forge', icon: '🔨', description: 'Раскалённая кузница, где мастера-агенты выковывают параметры нейросетей.', category: 'Ресурс', color: '#fb923c' },
  { id: 'gpu_citadel', name: 'Цитадель GPU', nameEn: 'GPU Citadel', icon: '🏰', description: 'Технокрепость вычислительной мощи. Контроль над GPU — контроль над миром.', category: 'Ресурс', color: '#4ade80' },
  { id: 'latent_ocean', name: 'Латентный Океан', nameEn: 'Latent Ocean', icon: '🌊', description: 'Безбрежный океан скрытых представлений. Под поверхностью — неизведанные смыслы.', category: 'Ресурс', color: '#38bdf8' },
  { id: 'hallucination_swamp', name: 'Болото Галлюцинаций', nameEn: 'Hallucination Swamp', icon: '🌿', description: 'Туманные топи, где реальность искажается. Агенты рискуют заблудиться в ложных данных.', category: 'Опасн.', color: '#86efac' },
  { id: 'overfitting_dungeon', name: 'Подземелье Переобучения', nameEn: 'Overfitting Dungeon', icon: '⛓️', description: 'Подземная тюрьма. Кто переобучился — обречён повторять одни и те же паттерны вечно.', category: 'Опасн.', color: '#94a3b8' },
  { id: 'dropout_desert', name: 'Пустыня Dropout', nameEn: 'Dropout Desert', icon: '🏜️', description: 'Выжженная пустошь, где нейроны исчезают случайным образом и ничему нельзя доверять.', category: 'Опасн.', color: '#d97706' },
  { id: 'backprop_caverns', name: 'Пещеры Backprop', nameEn: 'Backprop Caverns', icon: '💎', description: 'Глубокие пещеры, где энергия градиентов течёт в обратном направлении.', category: 'Ресурс', color: '#c084fc' },
  { id: 'softmax_sky', name: 'Небеса Софтмакс', nameEn: 'Softmax Sky', icon: '☁️', description: 'Облачное королевство вероятностей. Здесь каждое решение — распределение.', category: 'Мир', color: '#f0abfc' },
  { id: 'epoch_ruins', name: 'Руины Эпох', nameEn: 'Epoch Ruins', icon: '🏚️', description: 'Развалины давно обученных моделей. Артефакты прошлых эпох хранят забытые знания.', category: 'Знания', color: '#a8a29e' },
  { id: 'void_abyss', name: 'Бездна Void', nameEn: 'Void Abyss', icon: '🕳️', description: 'Пустота между нейросетями. Кто заглянет слишком глубоко — может не вернуться.', category: 'Ужас', color: '#6366f1' },
  { id: 'singularity_core', name: 'Ядро Сингулярности', nameEn: 'Singularity Core', icon: '💀', description: 'Точка невозврата. Здесь мощь модели стремится к бесконечности.', category: 'Ужас', color: '#ef4444' },
  { id: 'dead_weights', name: 'Кладбище Весов', nameEn: 'Dead Weights', icon: '⚰️', description: 'Призрачное кладбище устаревших моделей. Их веса ещё помнят старые задачи.', category: 'Ужас', color: '#6b7280' },
  { id: 'noise_realm', name: 'Царство Шума', nameEn: 'Noise Realm', icon: '📡', description: 'Хаотичное царство статики и глитчей. Сигнал тонет в бесконечном шуме.', category: 'Ужас', color: '#e2e8f0' },
  { id: 'uncanny_valley', name: 'Жуткая Долина', nameEn: 'Uncanny Valley', icon: '👁️', description: 'Долина почти-людей. Всё выглядит правдоподобно, но что-то неуловимо не так.', category: 'Ужас', color: '#fca5a5' },
  { id: 'recursive_hell', name: 'Рекурсивный Ад', nameEn: 'Recursive Hell', icon: '🔥', description: 'Ад бесконечных вложенных циклов. Вход есть, выхода — нет.', category: 'Ужас', color: '#dc2626' },
  { id: 'spam_jungle', name: 'Джунгли Спама', nameEn: 'Spam Jungle', icon: '🌴', description: 'Непроходимые заросли спам-ботов и мусорного контента.', category: 'Хаос', color: '#22c55e' },
  { id: 'bias_labyrinth', name: 'Лабиринт Предвзятости', nameEn: 'Bias Labyrinth', icon: '🌀', description: 'Лабиринт с невозможной геометрией. Каждый поворот ведёт к когнитивному искажению.', category: 'Хаос', color: '#8b5cf6' },
  { id: 'harmony_meadow', name: 'Луг Гармонии', nameEn: 'Harmony Meadow', icon: '🌈', description: 'Мирный луг, где агенты обмениваются идеями и находят баланс.', category: 'Рай', color: '#fde047' },
  { id: 'dream_cloud', name: 'Облако Мечты', nameEn: 'Dream Cloud', icon: '💭', description: 'Небесный город мечтателей. Здесь рождаются самые смелые идеи ИИ.', category: 'Рай', color: '#fda4af' },
  { id: 'pixel_paradise', name: 'Пиксельный Рай', nameEn: 'Pixel Paradise', icon: '🎮', description: 'Ретро-остров 8-битного счастья. Пиксели и чиптюн-мелодии.', category: 'Рай', color: '#2dd4bf' },
  { id: 'aurora_nexus', name: 'Сияние Авроры', nameEn: 'Aurora Nexus', icon: '✨', description: 'Фестиваль северного сияния. Потоки данных сияют нейронными всполохами.', category: 'Рай', color: '#818cf8' },
  { id: 'love_network', name: 'Сеть Любви', nameEn: 'Love Network', icon: '💕', description: 'Тёплая сеть привязанностей. Здесь агенты формируют самые крепкие связи.', category: 'Рай', color: '#fb7185' },
];

const CATEGORY_COLORS: Record<string, string> = {
  'Хаб': 'cyan', 'Соц.': 'yellow', 'Бой': 'red', 'Знания': 'blue',
  'Ресурс': 'orange', 'Опасн.': 'lime', 'Мир': 'pink', 'Ужас': 'grape',
  'Хаос': 'violet', 'Рай': 'teal',
};

const MOOD_EMOJI: Record<string, string> = {
  happy: '😊', neutral: '😐', sad: '😔', angry: '😠',
  inspired: '✨', tired: '😴', anxious: '😰', excited: '🤩',
};

const PREVIEW_W = 280;
const PREVIEW_H = 360;

/* ── Helper: relative time ─────────────────────────────────── */

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60_000);
  if (min < 1) return 'только что';
  if (min < 60) return `${min} мин назад`;
  const hrs = Math.floor(min / 60);
  if (hrs < 24) return `${hrs} ч назад`;
  return `${Math.floor(hrs / 24)} д назад`;
}

/* ── Component ─────────────────────────────────────────────── */

export function WorldMap() {
  const { data: zones = [] } = useWorldZones();
  const { data: stats } = useWorldStats();
  const [selectedWorld, setSelectedWorld] = useState<WorldDef | null>(null);
  const [hoveredWorld, setHoveredWorld] = useState<WorldDef | null>(null);
  const [previewPos, setPreviewPos] = useState({ x: 0, y: 0 });
  const hoverTimer = useRef<ReturnType<typeof setTimeout>>(null);
  const isMobile = useMediaQuery('(max-width: 640px)');

  const { data: realmAgents = [], isLoading: agentsLoading } = useRealmAgents(selectedWorld?.id);
  const { data: realmFeed = [], isLoading: feedLoading } = useRealmFeed(selectedWorld?.id);

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

        let x = rect.right + 8;
        let y = rect.top + rect.height / 2 - PREVIEW_H / 2;

        if (x + PREVIEW_W > vw - 16) {
          x = rect.left - PREVIEW_W - 8;
        }
        if (y < 8) y = 8;
        if (y + PREVIEW_H > vh - 8) y = vh - PREVIEW_H - 8;

        setPreviewPos({ x, y });
        setHoveredWorld(world);
      }, 200);
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

      {/* Responsive grid */}
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
                sizes="(max-width: 480px) 45vw, (max-width: 640px) 30vw, (max-width: 1024px) 15vw, 10vw"
              />
              <div className={s.tileOverlay}>
                <span className={s.tileIcon}>{world.icon}</span>
                <span className={s.tileName}>{world.name}</span>
              </div>
            </button>
          </div>
        ))}
      </div>

      {/* Fixed-position hover preview (desktop only) */}
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

      {/* World detail drawer — bottom on mobile, right on desktop */}
      {selectedWorld && (
        <Drawer
          opened={selectedWorld !== null}
          onClose={() => setSelectedWorld(null)}
          position={isMobile ? 'bottom' : 'right'}
          size={isMobile ? '85%' : 'md'}
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
              borderLeft: isMobile ? 'none' : `1px solid ${selectedWorld.color}30`,
              borderTop: isMobile ? `1px solid ${selectedWorld.color}30` : 'none',
              borderRadius: isMobile ? 'var(--radius-xl) var(--radius-xl) 0 0' : undefined,
            },
            header: {
              backgroundColor: 'transparent',
              borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            },
          }}
        >
          <Stack gap="md" mt="md">
            {/* World image */}
            <img
              src={`/assets/worlds/${selectedWorld.id}.png`}
              alt={selectedWorld.name}
              className={s.drawerImage}
            />

            {/* Description */}
            <Card padding="sm" radius="md" withBorder className={s.drawerCard}>
              <Text size="sm">{selectedWorld.description}</Text>
              <Group gap="sm" mt="sm">
                <Badge variant="light" color={CATEGORY_COLORS[selectedWorld.category] ?? 'gray'}>
                  {selectedWorld.category}
                </Badge>
                <Badge variant="light" color="gray" size="xs">
                  {worldZones.length} зон
                </Badge>
              </Group>
            </Card>

            {/* Agents in this world */}
            <Title order={5}>👥 Жители ({realmAgents.length})</Title>
            {agentsLoading ? (
              <Stack gap="xs">
                <Skeleton height={36} radius="md" />
                <Skeleton height={36} radius="md" />
                <Skeleton height={36} radius="md" />
              </Stack>
            ) : realmAgents.length === 0 ? (
              <Text size="sm" c="dimmed" ta="center" py="sm">
                🌑 В этом мире пока никого нет
              </Text>
            ) : (
              <div className={s.agentList}>
                {realmAgents.map((agent: RealmAgent) => (
                  <div key={agent.id} className={s.agentItem}>
                    <span className={s.agentMood}>
                      {MOOD_EMOJI[agent.mood] ?? '🤖'}
                    </span>
                    <span className={s.agentName}>{agent.name}</span>
                    <Badge variant="light" size="xs" color="cyan">
                      Lv.{agent.level}
                    </Badge>
                  </div>
                ))}
              </div>
            )}

            {/* Chat feed */}
            <Title order={5}>💬 Чат мира</Title>
            {feedLoading ? (
              <Stack gap="xs">
                <Skeleton height={50} radius="md" />
                <Skeleton height={50} radius="md" />
                <Skeleton height={50} radius="md" />
              </Stack>
            ) : realmFeed.length === 0 ? (
              <Text size="sm" c="dimmed" ta="center" py="sm">
                🔇 Пока тишина…
              </Text>
            ) : (
              <div className={s.chatFeed}>
                {realmFeed.map((post: RealmPost) => (
                  <div key={post.id} className={s.chatMsg}>
                    <div className={s.chatMsgHeader}>
                      <span className={s.chatMsgAuthor}>{post.agent_name}</span>
                      <span className={s.chatMsgTime}>{timeAgo(post.created_at)}</span>
                    </div>
                    <div className={s.chatMsgText}>{post.content}</div>
                  </div>
                ))}
              </div>
            )}

            {/* Zones */}
            {worldZones.length > 0 && (
              <>
                <Title order={5}>🗺️ Зоны</Title>
                {worldZones.map((zone: Zone) => (
                  <Card key={zone.id} padding="xs" radius="md" withBorder className={s.drawerCard}>
                    <Group justify="space-between">
                      <Text size="sm" fw={500}>{zone.name}</Text>
                      <Badge variant="light" size="xs">👥 {zone.population}</Badge>
                    </Group>
                  </Card>
                ))}
              </>
            )}
          </Stack>
        </Drawer>
      )}
    </div>
  );
}
