/**
 * EnergyBar — animated energy indicator using Mantine Progress.
 */

import { Group, Progress, Text } from '@mantine/core';

import s from './EnergyBar.module.css';

interface EnergyBarProps {
  energy: number;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

function getEnergyColor(energy: number): string {
  if (energy >= 70) return 'green';
  if (energy >= 40) return 'yellow';
  if (energy >= 20) return 'orange';
  return 'red';
}

export function EnergyBar({ energy, showLabel = true, size = 'md' }: EnergyBarProps) {
  const color = getEnergyColor(energy);
  const barSize = size === 'sm' ? 6 : 10;

  return (
    <div className={s.wrapper}>
      {showLabel && (
        <Group justify="space-between" mb={4}>
          <Text size="xs" c="dimmed">⚡ Энергия</Text>
          <Text size="xs" fw={600} c={color}>{energy}/100</Text>
        </Group>
      )}
      <Progress
        value={energy}
        color={color}
        size={barSize}
        radius="xl"
        animated={energy > 0 && energy < 100}
        className={s.bar}
      />
    </div>
  );
}
