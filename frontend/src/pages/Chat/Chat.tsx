import { type FormEvent, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { api } from '@/api/client';
import type { Agent, ChatResponse } from '@/api/types';

import s from './Chat.module.css';

interface Message {
  role: 'user' | 'agent';
  text: string;
}

export function Chat() {
  const { id } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentLoading, setAgentLoading] = useState(true);
  const messagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadAgent() {
      try {
        const data = await api.get<Agent>(`/api/v1/agents/${id}`);
        setAgent(data);
      } catch {
        // fail gracefully
      } finally {
        setAgentLoading(false);
      }
    }
    void loadAgent();
  }, [id]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesRef.current?.scrollTo({
      top: messagesRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages]);

  async function handleSend(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const response = await api.post<ChatResponse>(
        `/api/v1/chat/${id}`,
        { message: userMsg },
      );
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: response.reply },
      ]);
      // Update mood locally
      if (agent) {
        setAgent({ ...agent, mood: response.mood });
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'agent', text: '⚠️ Ошибка связи с агентом...' },
      ]);
    } finally {
      setLoading(false);
    }
  }

  if (agentLoading) {
    return <div className={s.loading}>⏳ Загрузка...</div>;
  }

  return (
    <div className={s.chatPage}>
      {/* Chat Header */}
      <div className={s.chatHeader}>
        <img
          src="/assets/agent-avatar.svg"
          alt={agent?.name ?? 'Agent'}
          className={s.chatAvatar}
        />
        <div>
          <div className={s.chatName}>{agent?.name ?? 'Агент'}</div>
          <div className={s.chatMood}>
            Настроение: {agent?.mood ?? 'neutral'} · Lv.{agent?.level ?? 1}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className={s.messages} ref={messagesRef}>
        {messages.length === 0 && (
          <div className={s.typing}>
            Начните разговор с {agent?.name ?? 'агентом'}...
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`${s.bubble} ${
              msg.role === 'user' ? s.bubbleUser : s.bubbleAgent
            }`}
          >
            {msg.text}
          </div>
        ))}
        {loading && <div className={s.typing}>💭 {agent?.name} думает...</div>}
      </div>

      {/* Input */}
      <form className={s.inputArea} onSubmit={handleSend}>
        <input
          className={s.chatInput}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напишите сообщение..."
          disabled={loading}
        />
        <button
          type="submit"
          className={s.sendBtn}
          disabled={loading || !input.trim()}
        >
          {loading ? '...' : '→'}
        </button>
      </form>
    </div>
  );
}
