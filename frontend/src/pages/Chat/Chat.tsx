import { type FormEvent, useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

import { useAgent, useChatMutation } from '@/hooks/useApi';
import { MoodBadge } from '@/components/MoodBadge/MoodBadge';
import { Skeleton } from '@/components/Skeleton/Skeleton';

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
    return (
      <div className={s.chatPage}>
        <div className={s.chatHeader}>
          <Skeleton variant="circle" width="44px" height="44px" />
          <div>
            <Skeleton variant="text" width="150px" height="16px" />
            <Skeleton variant="text" width="100px" height="12px" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={s.chatPage}>
      <div className={s.chatHeader}>
        <Link to={`/agent/${agent?.id}`} className={s.avatarLink}>
          <img
            src="/assets/agent-avatar.svg"
            alt={agent?.name ?? 'Agent'}
            className={s.chatAvatar}
          />
          <span className={s.onlineIndicator} />
        </Link>
        <div className={s.headerInfo}>
          <div className={s.chatName}>{agent?.name ?? 'Агент'}</div>
          <div className={s.chatStatus}>
            <MoodBadge mood={currentMood} size="sm" />
            <span className={s.chatLevel}>Lv.{agent?.level ?? 1}</span>
          </div>
        </div>
      </div>

      <div className={s.messages} ref={messagesRef}>
        {messages.length === 0 && (
          <div className={s.welcome}>
            <div className={s.welcomeIcon}>💬</div>
            <p className={s.welcomeText}>
              Начните разговор с {agent?.name ?? 'агентом'}
            </p>
            <p className={s.welcomeHint}>
              Агент ответит в своём характере и настроении
            </p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`${s.bubble} ${
              msg.role === 'user' ? s.bubbleUser : s.bubbleAgent
            }`}
          >
            {msg.role === 'agent' && (
              <img
                src="/assets/agent-avatar.svg"
                alt=""
                className={s.bubbleAvatar}
              />
            )}
            <div className={s.bubbleContent}>
              {msg.text}
            </div>
          </div>
        ))}
        {chatMutation.isPending && (
          <div className={`${s.bubble} ${s.bubbleAgent}`}>
            <img src="/assets/agent-avatar.svg" alt="" className={s.bubbleAvatar} />
            <div className={s.typingDots}>
              <span className={s.dot} />
              <span className={s.dot} />
              <span className={s.dot} />
            </div>
          </div>
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
          <span className={s.sendIcon}>↑</span>
        </button>
      </form>
    </div>
  );
}
