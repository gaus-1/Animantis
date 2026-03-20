/**
 * Chat — real-time chat interface with an AI agent.
 */

import { type FormEvent, useEffect, useRef, useState } from 'react';

import {
  ActionIcon,
  Avatar,
  Group,
  Loader,
  Skeleton,
  Text,
  TextInput,
} from '@mantine/core';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, Link } from 'react-router-dom';

import { useAgent, useChatMutation } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';

import s from './Chat.module.css';

interface Message {
  role: 'user' | 'agent';
  text: string;
}

export function Chat() {
  const { id } = useParams<{ id: string }>();
  const { data: agent, isLoading: agentLoading } = useAgent(id);
  const chatMutation = useChatMutation(id);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [currentMood, setCurrentMood] = useState('neutral');
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (agent?.mood) setCurrentMood(agent.mood);
  }, [agent?.mood]);

  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);

    try {
      const response = await chatMutation.mutateAsync(userMsg);
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: response.reply },
      ]);
      setCurrentMood(response.mood);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: '⚠️ Ошибка связи с агентом...' },
      ]);
    }
  }

  if (agentLoading) {
    return (
      <div className={s.chatPage}>
        <div className={s.chatHeader}>
          <Group gap="sm">
            <Skeleton circle height={44} />
            <div>
              <Skeleton width={150} height={16} mb={4} />
              <Skeleton width={100} height={12} />
            </div>
          </Group>
        </div>
      </div>
    );
  }

  return (
    <div className={s.chatPage}>
      {/* Header */}
      <div className={s.chatHeader}>
        <Group gap="sm" wrap="nowrap">
          <Link to={`/agent/${agent?.id}`} className={s.avatarLink}>
            <Avatar
              src="/assets/agent-avatar.svg"
              alt={agent?.name ?? 'Agent'}
              size="md"
              className={s.chatAvatar}
            />
            <span className={s.onlineIndicator} />
          </Link>
          <div>
            <Text fw={600} size="sm">{agent?.name ?? 'Агент'}</Text>
            <Group gap="xs">
              <MoodBadge mood={currentMood} size="xs" />
              <Text size="xs" c="dimmed">Lv.{agent?.level ?? 1}</Text>
            </Group>
          </div>
        </Group>
      </div>

      {/* Messages */}
      <div className={s.messages} ref={messagesRef}>
        {messages.length === 0 && (
          <div className={s.welcome}>
            <Text size="2rem" mb="sm">💬</Text>
            <Text fw={500}>Начните разговор с {agent?.name ?? 'агентом'}</Text>
            <Text size="sm" c="dimmed">
              Агент ответит в своём характере и настроении
            </Text>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 8, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.2 }}
              className={`${s.bubble} ${
                msg.role === 'user' ? s.bubbleUser : s.bubbleAgent
              }`}
            >
              {msg.role === 'agent' && (
                <Avatar
                  src="/assets/agent-avatar.svg"
                  size="sm"
                  className={s.bubbleAvatar}
                />
              )}
              <div className={s.bubbleContent}>{msg.text}</div>
            </motion.div>
          ))}
        </AnimatePresence>

        {chatMutation.isPending && (
          <div className={`${s.bubble} ${s.bubbleAgent}`}>
            <Avatar src="/assets/agent-avatar.svg" size="sm" className={s.bubbleAvatar} />
            <Loader type="dots" size="sm" color="cyan" />
          </div>
        )}
      </div>

      {/* Input */}
      <form className={s.inputArea} onSubmit={handleSend}>
        <TextInput
          className={s.chatInput}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напишите сообщение..."
          disabled={chatMutation.isPending}
          radius="xl"
          size="md"
          styles={{
            input: {
              backgroundColor: 'rgba(12, 18, 34, 0.85)',
              borderColor: 'rgba(255, 255, 255, 0.08)',
            },
          }}
        />
        <ActionIcon
          type="submit"
          variant="filled"
          color="cyan"
          size="lg"
          radius="xl"
          disabled={chatMutation.isPending || !input.trim()}
          className={s.sendBtn}
        >
          ↑
        </ActionIcon>
      </form>
    </div>
  );
}
