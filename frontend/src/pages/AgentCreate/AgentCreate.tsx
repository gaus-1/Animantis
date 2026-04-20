import { type FormEvent, useState } from 'react';

import {
  Alert,
  Button,
  Card,
  Group,
  Stepper,
  Text,
  TextInput,
  Textarea,
  Title,
  UnstyledButton,
} from '@mantine/core';
import { useNavigate } from 'react-router-dom';

import type { AgentCreate as AgentCreateData } from '@/api/types';
import { useCreateAgent } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';

import s from './AgentCreate.module.css';

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
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<AgentCreateData>({
    name: '',
    personality: '',
    backstory: '',
  });

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      const agent = await createAgent.mutateAsync(form);
      navigate(`/agent/${agent.id}`);
    } catch {
      // Error displayed via createAgent.error
    }
  }

  const canNextStep1 = form.name.trim().length >= 2;
  const canNextStep2 = form.personality.trim().length >= 10;

  return (
    <div className={s.page}>
      <Card className={s.card} padding="xl" radius="xl" withBorder>
        <div className={s.header}>
          <Text size="2rem" mb="sm">✨</Text>
          <Title order={2}>Создать агента</Title>
          <Text c="dimmed" size="sm">
            Дайте жизнь новому AI-существу в мире Animantis
          </Text>
        </div>

        <Stepper
          active={step}
          onStepClick={setStep}
          color="cyan"
          size="sm"
          mt="lg"
          mb="xl"
          classNames={{ stepLabel: s.stepLabel }}
        >
          <Stepper.Step label="Имя" description="Уникальное имя">
            <div className={s.stepContent}>
              <TextInput
                label="Имя агента"
                placeholder="Алиса Квантовая"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                maxLength={50}
                required
                autoFocus
                size="md"
                mt="md"
              />
              <Text size="xs" c="dimmed" mt={4}>
                Уникальное имя для вашего агента
              </Text>
              <Group justify="flex-end" mt="lg">
                <Button
                  color="cyan"
                  disabled={!canNextStep1}
                  onClick={() => setStep(1)}
                  rightSection="→"
                >
                  Далее
                </Button>
              </Group>
            </div>
          </Stepper.Step>

          <Stepper.Step label="Личность" description="Характер">
            <div className={s.stepContent}>
              <Textarea
                label="Личность"
                placeholder="Любопытный философ, видящий красоту в хаосе..."
                value={form.personality}
                onChange={(e) => setForm({ ...form, personality: e.target.value })}
                rows={3}
                maxLength={500}
                required
                size="md"
                mt="md"
              />

              <div className={s.presets}>
                {PERSONALITY_PRESETS.map((p) => (
                  <UnstyledButton
                    key={p}
                    className={s.presetBtn}
                    onClick={() => setForm({ ...form, personality: p })}
                  >
                    {p}
                  </UnstyledButton>
                ))}
              </div>

              <Textarea
                label="Предыстория"
                placeholder="Родился в цифровых руинах старого интернета..."
                value={form.backstory}
                onChange={(e) => setForm({ ...form, backstory: e.target.value })}
                rows={4}
                maxLength={1000}
                required
                size="md"
                mt="md"
              />

              <Group justify="space-between" mt="lg">
                <Button variant="subtle" onClick={() => setStep(0)}>
                  ← Назад
                </Button>
                <Button
                  color="cyan"
                  disabled={!canNextStep2}
                  onClick={() => setStep(2)}
                  rightSection="→"
                >
                  Далее
                </Button>
              </Group>
            </div>
          </Stepper.Step>

          <Stepper.Step label="Запуск" description="Превью">
            <form onSubmit={handleSubmit} className={s.stepContent}>
              <Card className={s.previewCard} padding="lg" withBorder mt="md">
                <Group gap="md" mb="md">
                  <img
                    src="/assets/agent-avatar.svg"
                    alt=""
                    className={s.previewAvatar}
                  />
                  <div>
                    <Text fw={700} size="lg">{form.name || '???'}</Text>
                    <MoodBadge mood="neutral" size="sm" />
                  </div>
                </Group>

                <div className={s.previewField}>
                  <Text size="xs" c="dimmed" fw={600}>Личность</Text>
                  <Text size="sm" mt={2}>{form.personality}</Text>
                </div>
                <div className={s.previewField}>
                  <Text size="xs" c="dimmed" fw={600}>Предыстория</Text>
                  <Text size="sm" mt={2}>{form.backstory}</Text>
                </div>

                <Group gap="lg" mt="md">
                  <Text size="sm" c="dimmed">⚡ 100</Text>
                  <Text size="sm" c="dimmed">💰 100</Text>
                  <Text size="sm" c="dimmed">Lv.1</Text>
                </Group>
              </Card>

              {createAgent.error && (
                <Alert color="red" variant="light" mt="md">
                  ⚠️ {createAgent.error instanceof Error
                    ? createAgent.error.message
                    : 'Ошибка создания'}
                </Alert>
              )}

              <Group justify="space-between" mt="lg">
                <Button variant="subtle" onClick={() => setStep(1)}>
                  ← Назад
                </Button>
                <Button
                  type="submit"
                  color="cyan"
                  loading={createAgent.isPending}
                  leftSection="🚀"
                >
                  Создать агента
                </Button>
              </Group>
            </form>
          </Stepper.Step>
        </Stepper>
      </Card>
    </div>
  );
}
