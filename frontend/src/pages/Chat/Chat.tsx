import { type FormEvent, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

import { useAgent, useChatMutation } from '@/hooks/useApi';

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

  // Sync mood from agent data
  useEffect(() => {
    if (agent?.mood) setCurrentMood(agent.mood);
  }, [agent?.mood]);

  // Auto-scroll to bottom
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
    return <div className={s.loading}>⏳ Загрузка...</div>;
  }

  return (
    <div className={s.chatPage}>
      <div className={s.chatHeader}>
        <img
          src="/assets/agent-avatar.svg"
          alt={agent?.name ?? 'Agent'}
          className={s.chatAvatar}
        />
        <div>
          <div className={s.chatName}>{agent?.name ?? 'Агент'}</div>
          <div className={s.chatMood}>
            Настроение: {currentMood} · Lv.{agent?.level ?? 1}
          </div>
        </div>
      </div>

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
        {chatMutation.isPending && (
          <div className={s.typing}>💭 {agent?.name} думает...</div>
        )}
      </div>

      <form className={s.inputArea} onSubmit={handleSend}>
        <input
          className={s.chatInput}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Напишите сообщение..."
          disabled={chatMutation.isPending}
        />
        <button
          type="submit"
          className={s.sendBtn}
          disabled={chatMutation.isPending || !input.trim()}
        >
          {chatMutation.isPending ? '...' : '→'}
        </button>
      </form>
    </div>
  );
}
