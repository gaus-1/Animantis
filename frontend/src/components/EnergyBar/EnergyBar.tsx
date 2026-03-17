/**
 * EnergyBar — animated energy level indicator.
 *
 * Gradient fill: green → yellow → red based on energy level.
 * Micro-animation on value change.
 */

import s from './EnergyBar.module.css';

interface EnergyBarProps {
  energy: number;
  maxEnergy?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

function getEnergyClass(percent: number): string {
  if (percent > 60) return s.high;
  if (percent > 30) return s.medium;
  return s.low;
}

export function EnergyBar({ energy, maxEnergy = 100, showLabel = true, size = 'md' }: EnergyBarProps) {
  const percent = Math.min(100, Math.max(0, (energy / maxEnergy) * 100));

  return (
    <div className={`${s.container} ${s[size]}`}>
      {showLabel && (
        <span className={s.label}>⚡ {energy}/{maxEnergy}</span>
      )}
      <div className={s.track}>
        <div
          className={`${s.fill} ${getEnergyClass(percent)}`}
          data-width={`${percent}%`}
          style={{ '--energy-width': `${percent}%` } as React.CSSProperties}
        />
      </div>
    </div>
  );
}
