import { type FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import type { AgentCreate as AgentCreateData } from '@/api/types';
import { useCreateAgent } from '@/hooks/useApi';

import s from './AgentCreate.module.css';

export function AgentCreate() {
  const navigate = useNavigate();
  const createAgent = useCreateAgent();
  const [form, setForm] = useState<AgentCreateData>({
    name: '',
    personality: '',
    backstory: '',
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      // Get user_id from Telegram WebApp, default to 1 for out-of-tg local testing
      const tgUserId = (window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id || 1;

      const payload = {
        ...form,
        user_id: tgUserId,
      };

      const agent = await createAgent.mutateAsync(payload);
      navigate(`/agent/${agent.id}`);
    } catch {
      // Error handled via createAgent.error
    }
  }

  return (
    <div className={s.page}>
      <div className={s.card}>
        <div className={s.header}>
          <div className={s.headerIcon}>✨</div>
          <h1 className={s.title}>Создать агента</h1>
          <p className={s.subtitle}>
            Дайте жизнь новому AI-существу в мире Animantis
          </p>
        </div>

        <form onSubmit={handleSubmit} className={s.form}>
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
            />
            <span className={s.hint}>Уникальное имя для вашего агента</span>
          </div>

          <div className={s.field}>
            <label className={s.label} htmlFor="personality">Личность</label>
            <textarea
              id="personality"
              className={s.textarea}
              value={form.personality}
              onChange={(e) => setForm({ ...form, personality: e.target.value })}
              placeholder="Любопытный философ, который видит красоту в хаосе..."
              rows={3}
              maxLength={500}
              required
            />
            <span className={s.hint}>Кто ваш агент? Что им движет?</span>
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
            <span className={s.hint}>Откуда пришёл? Что пережил?</span>
          </div>

          {createAgent.error && (
            <div className={s.error}>
              ⚠️ {createAgent.error instanceof Error
                ? createAgent.error.message
                : 'Ошибка создания'}
            </div>
          )}

          <button
            type="submit"
            className={s.submitBtn}
            disabled={createAgent.isPending}
          >
            {createAgent.isPending ? '⏳ Создаём...' : '🚀 Создать агента'}
          </button>
        </form>
      </div>
    </div>
  );
}
