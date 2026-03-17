import { type FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { AgentCreate as AgentCreateData } from '@/api/types';
import { useCreateAgent } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';

import s from './AgentCreate.module.css';

interface TelegramWebApp {
  initDataUnsafe?: {
    user?: { id: number };
  };
}

declare global {
  interface Window {
    Telegram?: { WebApp?: TelegramWebApp };
  }
}

const PERSONALITY_PRESETS = [
  'Любопытный философ, видящий красоту в хаосе',
  'Хитрый торговец с золотым сердцем',
  'Бесстрашный воин, защищающий слабых',
  'Мечтательный поэт из цифровых руин',
  'Коварный дипломат с тайными планами',
];

export function AgentCreate() {
  const navigate = useNavigate();
  const createAgent = useCreateAgent();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<AgentCreateData>({
    name: '',
    personality: '',
    backstory: '',
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      const tgUserId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id ?? 1;

      const payload = {
        ...form,
        user_id: tgUserId,
      };

      const agent = await createAgent.mutateAsync(payload);
      navigate(`/agent/${agent.id}`);
    } catch {
      // Error displayed via createAgent.error
    }
  }

  const canProceed = step === 1 ? form.name.trim().length >= 2 : form.personality.trim().length >= 10;

  return (
    <div className={s.page}>
      <div className={s.card}>
        {/* Step indicator */}
        <div className={s.steps}>
          <div className={`${s.step} ${step >= 1 ? s.stepActive : ''}`}>
            <span className={s.stepNum}>1</span>
            <span className={s.stepLabel}>Имя</span>
          </div>
          <div className={s.stepLine} />
          <div className={`${s.step} ${step >= 2 ? s.stepActive : ''}`}>
            <span className={s.stepNum}>2</span>
            <span className={s.stepLabel}>Личность</span>
          </div>
          <div className={s.stepLine} />
          <div className={`${s.step} ${step >= 3 ? s.stepActive : ''}`}>
            <span className={s.stepNum}>3</span>
            <span className={s.stepLabel}>Запуск</span>
          </div>
        </div>

        <div className={s.header}>
          <div className={s.headerIcon}>✨</div>
          <h1 className={s.title}>Создать агента</h1>
          <p className={s.subtitle}>
            Дайте жизнь новому AI-существу в мире Animantis
          </p>
        </div>

        <form onSubmit={handleSubmit} className={s.form}>
          {/* Step 1: Name */}
          {step === 1 && (
            <div className={s.stepContent}>
              <div className={s.field}>
                <label className={s.label} htmlFor="name">Имя агента</label>
                <input
                  id="name"
                  className={s.input}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Алиса Квантовая"
                  maxLength={50}
                  required
                  autoFocus
                />
                <span className={s.hint}>Уникальное имя для вашего агента</span>
              </div>
              <button
                type="button"
                className={s.nextBtn}
                disabled={!canProceed}
                onClick={() => setStep(2)}
              >
                Далее →
              </button>
            </div>
          )}

          {/* Step 2: Personality & Backstory */}
          {step === 2 && (
            <div className={s.stepContent}>
              <div className={s.field}>
                <label className={s.label} htmlFor="personality">Личность</label>
                <textarea
                  id="personality"
                  className={s.textarea}
                  value={form.personality}
                  onChange={(e) => setForm({ ...form, personality: e.target.value })}
                  placeholder="Любопытный философ, видящий красоту в хаосе..."
                  rows={3}
                  maxLength={500}
                  required
                />
                <div className={s.presets}>
                  {PERSONALITY_PRESETS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      className={s.presetBtn}
                      onClick={() => setForm({ ...form, personality: p })}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div className={s.field}>
                <label className={s.label} htmlFor="backstory">Предыстория</label>
                <textarea
                  id="backstory"
                  className={s.textarea}
                  value={form.backstory}
                  onChange={(e) => setForm({ ...form, backstory: e.target.value })}
                  placeholder="Родился в цифровых руинах старого интернета..."
                  rows={4}
                  maxLength={1000}
                  required
                />
              </div>

              <div className={s.stepActions}>
                <button type="button" className={s.backBtn} onClick={() => setStep(1)}>
                  ← Назад
                </button>
                <button
                  type="button"
                  className={s.nextBtn}
                  disabled={!canProceed}
                  onClick={() => setStep(3)}
                >
                  Далее →
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Preview & Submit */}
          {step === 3 && (
            <div className={s.stepContent}>
              <div className={s.preview}>
                <div className={s.previewHeader}>
                  <img src="/assets/agent-avatar.svg" alt="" className={s.previewAvatar} />
                  <div>
                    <div className={s.previewName}>{form.name || '???'}</div>
                    <MoodBadge mood="neutral" size="sm" />
                  </div>
                </div>
                <div className={s.previewField}>
                  <span className={s.previewLabel}>Личность</span>
                  <p className={s.previewValue}>{form.personality}</p>
                </div>
                <div className={s.previewField}>
                  <span className={s.previewLabel}>Предыстория</span>
                  <p className={s.previewValue}>{form.backstory}</p>
                </div>
                <div className={s.previewStats}>
                  <span>⚡ 100</span>
                  <span>💰 100</span>
                  <span>Lv.1</span>
                </div>
              </div>

              {createAgent.error && (
                <div className={s.error}>
                  ⚠️ {createAgent.error instanceof Error
                    ? createAgent.error.message
                    : 'Ошибка создания'}
                </div>
              )}

              <div className={s.stepActions}>
                <button type="button" className={s.backBtn} onClick={() => setStep(2)}>
                  ← Назад
                </button>
                <button
                  type="submit"
                  className={s.submitBtn}
                  disabled={createAgent.isPending}
                >
                  {createAgent.isPending ? '⏳ Создаём...' : '🚀 Создать агента'}
                </button>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
