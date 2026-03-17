/**
 * Skeleton — shimmer loading placeholder.
 *
 * Replaces content while loading with a smooth animation.
 */

import s from './Skeleton.module.css';

interface SkeletonProps {
  variant?: 'text' | 'circle' | 'rect' | 'card' | 'post';
  width?: string;
  height?: string;
  count?: number;
}

function SkeletonBase({ width, height, className }: { width?: string; height?: string; className: string }) {
  return (
    <div
      className={`${s.skeleton} ${className}`}
      style={{ '--sk-w': width, '--sk-h': height } as React.CSSProperties}
    />
  );
}

export function Skeleton({ variant = 'text', width, height, count = 1 }: SkeletonProps) {
  if (variant === 'post') {
    return (
      <div className={s.postSkeleton}>
        <div className={s.postHeader}>
          <SkeletonBase className={s.circle} width="36px" height="36px" />
          <div className={s.postMeta}>
            <SkeletonBase className={s.text} width="120px" height="14px" />
            <SkeletonBase className={s.text} width="80px" height="10px" />
          </div>
        </div>
        <SkeletonBase className={s.rect} width="100%" height="60px" />
        <div className={s.postActions}>
          <SkeletonBase className={s.text} width="60px" height="12px" />
          <SkeletonBase className={s.text} width="80px" height="12px" />
        </div>
      </div>
    );
  }

  if (variant === 'card') {
    return (
      <div className={s.cardSkeleton}>
        <SkeletonBase className={s.circle} width="40px" height="40px" />
        <div className={s.cardInfo}>
          <SkeletonBase className={s.text} width="100px" height="14px" />
          <SkeletonBase className={s.text} width="140px" height="10px" />
          <SkeletonBase className={s.rect} width="100%" height="6px" />
        </div>
      </div>
    );
  }

  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <>
      {items.map((i) => (
        <SkeletonBase
          key={i}
          className={s[variant]}
          width={width}
          height={height}
        />
      ))}
    </>
  );
}
