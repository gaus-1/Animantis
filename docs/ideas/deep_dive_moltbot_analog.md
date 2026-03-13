# 🧠 DEEP DIVE: Аналог MoltBot/OpenClaw для РФ
## Полный технический анализ, стоимость, план реализации

---

## Часть 1: Архитектура OpenClaw — разбор до винтика

### Как устроен OpenClaw (270 000 ⭐ GitHub)

OpenClaw — это **headless Node.js сёрвис** с 3-слойной архитектурой:

```
┌─────────────────────────────────────────────────────────────────┐
│                    СЛОЙ 1: GATEWAY                              │
│  (Точка входа — Node.js, постоянно работает в фоне)            │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ WhatsApp │ │ Telegram │ │ Discord  │ │ iMessage │           │
│  │ Adapter  │ │ Adapter  │ │ Adapter  │ │ Adapter  │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       └─────────────┴─────────────┴────────────┘                │
│                          │                                       │
│            ┌─────────────▼──────────────┐                        │
│            │      Lane Queue            │                        │
│            │ (серийное исполнение —     │                        │
│            │  предотвращение гонок)     │                        │
│            └─────────────┬──────────────┘                        │
├──────────────────────────┼──────────────────────────────────────┤
│                    СЛОЙ 2: REASONING                             │
│  (Мозг — оркестрация LLM)                                       │
│                                                                  │
│            ┌─────────────▼──────────────┐                        │
│            │     Agent Runner           │                        │
│            │  • Собирает «мега-промпт»  │                        │
│            │  • Включает: инструкции,   │                        │
│            │    скиллы, память,          │                        │
│            │    состояние системы        │                        │
│            │  • context window guard    │                        │
│            └─────────────┬──────────────┘                        │
│                          │                                       │
│    ┌────────────┬────────┴────────┬────────────┐                │
│    ▼            ▼                 ▼            ▼                │
│ ┌──────┐  ┌──────────┐  ┌──────────┐  ┌────────┐              │
│ │Claude│  │ GPT-4o   │  │ Llama    │  │ Gemini │              │
│ └──────┘  └──────────┘  └──────────┘  └────────┘              │
├──────────────────────────┼──────────────────────────────────────┤
│                    СЛОЙ 3: EXECUTION                             │
│  (Руки — выполнение действий)                                   │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Файловая  │ │Терминал  │ │ Браузер  │ │   API    │           │
│  │ система  │ │(shell)   │ │(Puppeteer│ │ (HTTP)   │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│                                                                  │
│  ┌──────────────────────────────────────────────┐               │
│  │              SKILLS (50+ встроенных)          │               │
│  │  Markdown-файлы с инструкциями для агента    │               │
│  │  ~/.openclaw/skills/SKILL.md                  │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
│  ┌──────────────────────────────────────────────┐               │
│  │              MEMORY SYSTEM                    │               │
│  │                                              │               │
│  │  Ephemeral:                                   │               │
│  │  • memory/YYYY-MM-DD.md (дневные логи)       │               │
│  │  • session.jsonl (история сессий)             │               │
│  │                                              │               │
│  │  Durable:                                     │               │
│  │  • MEMORY.md (предпочтения, решения)          │               │
│  │  • soul.file (личность агента)                │               │
│  │  • USER.md (профиль пользователя)             │               │
│  └──────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### Критические проблемы OpenClaw (с Reddit)

| Проблема | Цитата | Наш ответ |
|---|---|---|
| 💸 $300–750/мес | «Burns tokens like a jet engine, 8M tokens on Claude-4.5-OPUS» | YandexGPT в 50x дешевле |
| 🔒 Безопасность | «Security nightmare, prompt injection, data erasure risk» | Sandbox + permissions |
| 🛠 «Vibe coded» | «Redundant info storage, invalid model selection possible» | Production-grade Python |
| 📖 Плохая документация | «Very bad docs, setup failures, API errors» | Русская документация |
| 👤 Только self-hosted | Нужен VPS, Node.js 22+, CLI | Облачный SaaS через Telegram |
| 🚫 Только 1 юзер | Нет multi-tenancy | Многопользовательская платформа |

---

## Часть 2: Адаптация под стек PandaPal

### Маппинг: OpenClaw → Наш стек

| Компонент OpenClaw | Технология OC | Наша замена (стек PandaPal) | Почему |
|---|---|---|---|
| **Gateway** | Node.js | **Python + aiohttp / FastAPI** | Уже знаешь; FastAPI для новых эндпоинтов |
| **Messaging** | WhatsApp, iMessage | **Telegram Bot API (python-telegram-bot / aiogram)** | Уже есть в PandaPal |
| **LLM** | Claude, GPT-4o | **YandexGPT + GigaChat + fallback на OpenAI** | Суверенность + дёшево |
| **Memory (ephemeral)** | Markdown-файлы на диске | **Redis** | Уже настроен, быстрее файлов |
| **Memory (durable)** | MEMORY.md файл | **PostgreSQL + pgvector** | Уже есть, семантический поиск |
| **Skills** | SKILL.md файлы | **Python-модули + MCP-серверы** | Код > Markdown, MCP = стандарт |
| **Shell execution** | Node.js child_process | **subprocess / asyncio.create_subprocess** | Нативный Python |
| **Browser** | Puppeteer (JS) | **Playwright (Python)** | Лучшая поддержка, async |
| **Queue** | Lane Queue (custom) | **Redis Queue (rq) / Celery** | Battle-tested |
| **Config** | YAML/JSON файлы | **Pydantic Settings + .env** | Валидация, type safety |

### Что менять в PandaPal

> [!IMPORTANT]
> Основной стек PandaPal **остаётся как есть**. Добавляем новые модули, не меняя существующие.

| Изменение | Тип | Детали |
|---|---|---|
| aiohttp → **добавить FastAPI** | ➕ Добавить | FastAPI для API-эндпоинтов (управление агентами, маркетплейс). aiohttp остаётся для Telegram-бота |
| **Agent Runtime** | ➕ Новый модуль | Оркестратор: принимает сообщение → строит промпт → вызывает LLM → исполняет tools |
| **Skills System** | ➕ Новый модуль | Загрузка/выполнение skill-модулей (Python-классы вместо Markdown) |
| **Memory Manager** | 🔄 Расширить | Добавить персистентную память агента в PostgreSQL (таблица `agent_memory`) |
| **Tool Executor** | ➕ Новый модуль | Sandbox для безопасного исполнения: subprocess, Playwright, HTTP |
| **MCP Client** | ➕ Новый модуль | Подключение к внешним MCP-серверам (WB, Ozon и т.д.) |

---

## Часть 3: Архитектура нашей платформы

```
┌─────────────────────────────────────────────────────────────────┐
│                      USERS (Telegram)                            │
│         User A          User B          User C                   │
│           │               │               │                      │
│           ▼               ▼               ▼                      │
│  ┌─────────────────────────────────────────────┐                │
│  │         TELEGRAM BOT (aiogram / PTB)        │                │
│  │         + Telegram Mini App (React)          │                │
│  └──────────────────┬──────────────────────────┘                │
│                     │                                            │
│  ┌──────────────────▼──────────────────────────┐                │
│  │         GATEWAY (FastAPI)                    │                │
│  │  • Аутентификация (Telegram user_id)         │                │
│  │  • Router: messages → Agent Runtime          │                │
│  │  • REST API для TMA                           │                │
│  │  • WebSocket для live-обновлений             │                │
│  └──────────────────┬──────────────────────────┘                │
│                     │                                            │
│  ┌──────────────────▼──────────────────────────┐                │
│  │         AGENT RUNTIME (Python)               │                │
│  │                                              │                │
│  │  ┌────────────────────────────┐              │                │
│  │  │ Prompt Builder             │              │                │
│  │  │ • System prompt            │              │                │
│  │  │ • User context (memory)    │              │                │
│  │  │ • Available skills/tools   │              │                │
│  │  │ • Current conversation     │              │                │
│  │  └────────────┬───────────────┘              │                │
│  │               │                               │                │
│  │  ┌────────────▼───────────────┐              │                │
│  │  │ LLM Router                 │              │                │
│  │  │ • Простые → YandexGPT Lite │              │                │
│  │  │ • Средние → YandexGPT Pro  │              │                │
│  │  │ • Сложные → GigaChat Pro   │              │                │
│  │  │ • Fallback → OpenAI GPT-4o │              │                │
│  │  └────────────┬───────────────┘              │                │
│  │               │                               │                │
│  │  ┌────────────▼───────────────┐              │                │
│  │  │ Tool Executor (Sandbox)    │              │                │
│  │  │ • MCP Client → WB/Ozon MCP│              │                │
│  │  │ • HTTP → внешние API       │              │                │
│  │  │ • Shell → ограниченный     │              │                │
│  │  │ • Browser → Playwright     │              │                │
│  │  └────────────────────────────┘              │                │
│  └──────────────────────────────────────────────┘                │
│                     │                                            │
│  ┌──────────────────▼──────────────────────────┐                │
│  │         DATA LAYER                           │                │
│  │                                              │                │
│  │  ┌──────────┐  ┌────────────┐  ┌──────────┐ │                │
│  │  │PostgreSQL│  │   Redis    │  │ pgvector │ │                │
│  │  │• Users   │  │• Sessions  │  │• Embeddings│                │
│  │  │• Agents  │  │• Cache     │  │• Semantic │ │                │
│  │  │• Memory  │  │• Queue     │  │  Search   │ │                │
│  │  │• Skills  │  │• Rate Limit│  │           │ │                │
│  │  └──────────┘  └────────────┘  └──────────┘ │                │
│  └──────────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Часть 4: Стоимость создания

### Вариант A: Бесплатно (аналогично PandaPal)

| Статья | Стоимость | Как |
|---|---|---|
| **Хостинг** | 0₽ | Oracle Cloud Free Tier / Amvera (бесплатный тариф) |
| **PostgreSQL** | 0₽ | Neon.tech Free Tier (0.5 GB) или Supabase |
| **Redis** | 0₽ | Upstash Free Tier (10K команд/день) — как в PandaPal |
| **Telegram Bot** | 0₽ | Бесплатный |
| **YandexGPT API** | 0₽ первые месяцы | Бесплатный грант ~6000₽ при регистрации Yandex Cloud |
| **Домен** | 0₽ | subdomain.vercel.app или без домена (только Telegram) |
| **Python / FastMCP / FastAPI** | 0₽ | Open source |
| **IDE** | 0₽ | VS Code / PyCharm Community |
| **GitHub** | 0₽ | Бесплатный |
| **ИТОГО** | **0₽** | |

### Вариант B: Минимальный Production (~2000₽/мес)

| Статья | Стоимость/мес | Что |
|---|---|---|
| **VPS (Timeweb/Selectel)** | ~500₽ | 2 CPU, 4GB RAM |
| **YandexGPT API** | ~1000₽ | ~500К токенов/день (достаточно для ~100 юзеров) |
| **Домен .ru** | ~100₽/мес | agentika.ru |
| **Upstash Redis** | 0₽ | Free tier хватит |
| **PostgreSQL** | 0₽ | На том же VPS |
| **ИТОГО** | **~1600₽/мес** | |

### Вариант C: Масштабирование (~10 000₽/мес при 1000 юзеров)

| Статья | Стоимость/мес | Что |
|---|---|---|
| **VPS** | ~2000₽ | 4 CPU, 8GB RAM |
| **YandexGPT API** | ~6000₽ | ~5M токенов/день |
| **Managed PostgreSQL** | ~1500₽ | Yandex Cloud |
| **Redis** | ~500₽ | Upstash Pro |
| **ИТОГО** | **~10 000₽/мес** | Окупается с 10 Pro-подписчиков |

---

## Часть 5: Структура проекта

```
agentika/
├── bot/                          # Telegram Bot (из PandaPal, адаптировать)
│   ├── __init__.py
│   ├── handlers/
│   │   ├── start.py             # /start, онбординг
│   │   ├── message.py           # Любое сообщение → Agent Runtime
│   │   └── settings.py          # Настройки агента
│   └── middleware/
│       ├── auth.py              # Telegram user_id → User
│       └── rate_limit.py        # Redis rate limiting (из PandaPal)
│
├── agent/                        # НОВЫЙ: Agent Runtime
│   ├── __init__.py
│   ├── runtime.py               # Главный цикл: message → LLM → tools → response
│   ├── prompt_builder.py        # Сборка мега-промпта (инструкции + память + скиллы)
│   ├── llm_router.py            # Выбор модели: простой → Lite, сложный → Pro
│   ├── tool_executor.py         # Sandbox-исполнение инструментов
│   └── memory_manager.py        # CRUD для памяти агента (PostgreSQL + Redis)
│
├── skills/                       # НОВЫЙ: Система скиллов
│   ├── __init__.py
│   ├── base.py                  # BaseSkill — абстрактный класс
│   ├── builtin/
│   │   ├── weather.py           # Погода (OpenWeatherMap)
│   │   ├── reminder.py          # Напоминания (Redis scheduled)
│   │   ├── web_search.py        # Поиск (Yandex Search API)
│   │   ├── summarize.py         # Суммаризация URL
│   │   └── calculator.py        # Расчёты
│   └── marketplace/
│       ├── loader.py            # Загрузка скиллов из маркетплейса
│       └── registry.py          # Реестр доступных скиллов
│
├── mcp/                          # НОВЫЙ: MCP-клиент
│   ├── __init__.py
│   ├── client.py                # Подключение к MCP-серверам
│   └── registry.py              # Реестр подключённых MCP-серверов
│
├── api/                          # НОВЫЙ: FastAPI для TMA и внешних API
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── routes/
│   │   ├── agents.py            # CRUD агентов
│   │   ├── skills.py            # Маркетплейс скиллов
│   │   ├── memory.py            # Просмотр памяти агента
│   │   └── analytics.py         # Статистика использования
│   └── deps.py                  # Зависимости (DB, Redis)
│
├── db/                           # База данных (расширить PandaPal)
│   ├── models.py                # SQLAlchemy модели
│   ├── migrations/              # Alembic миграции
│   └── connection.py            # PostgreSQL + pgvector подключение
│
├── config/                       # Конфигурация (из PandaPal)
│   ├── settings.py              # Pydantic BaseSettings
│   └── .env.example
│
├── tma/                          # Telegram Mini App (из PandaPal)
│   ├── src/
│   └── package.json
│
├── docker-compose.yml            # PostgreSQL + Redis + App
├── requirements.txt
└── README.md
```

---

## Часть 6: Модели базы данных

```python
# db/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String(255))
    plan = Column(String(50), default="free")  # free, pro, business
    created_at = Column(DateTime, server_default=func.now())
    agents = relationship("Agent", back_populates="user")

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), default="Помощник")
    system_prompt = Column(Text)          # Личность агента (аналог soul.file)
    model_preference = Column(String(50)) # yandexgpt-lite, yandexgpt-pro, gigachat
    is_active = Column(Boolean, default=True)
    skills = Column(JSON, default=[])     # Список подключённых скиллов
    mcp_servers = Column(JSON, default=[])# Список подключённых MCP-серверов
    user = relationship("User", back_populates="agents")
    memories = relationship("AgentMemory", back_populates="agent")

class AgentMemory(Base):
    __tablename__ = "agent_memories"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    content = Column(Text)                # Текст воспоминания
    category = Column(String(50))         # preference, fact, task, conversation
    embedding = Column(Vector(1024))      # Для семантического поиска (pgvector)
    created_at = Column(DateTime, server_default=func.now())
    agent = relationship("Agent", back_populates="memories")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    description = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"))
    code = Column(Text)                   # Python-код скилла
    price = Column(Integer, default=0)    # 0 = бесплатный
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0)
    is_public = Column(Boolean, default=True)

class ConversationLog(Base):
    __tablename__ = "conversation_logs"
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    role = Column(String(20))             # user, assistant, tool
    content = Column(Text)
    tool_calls = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    model_used = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
```

---

## Часть 7: Agent Runtime — ядро системы

```python
# agent/runtime.py (упрощённый псевдокод)
class AgentRuntime:
    def __init__(self, agent: Agent, db, redis, llm_router, tool_executor):
        self.agent = agent
        self.db = db
        self.redis = redis
        self.llm_router = llm_router
        self.tool_executor = tool_executor
        self.prompt_builder = PromptBuilder(agent)
        self.memory_manager = MemoryManager(agent, db)

    async def process_message(self, user_message: str) -> str:
        # 1. Загрузить релевантные воспоминания (pgvector поиск)
        memories = await self.memory_manager.recall(user_message, limit=5)

        # 2. Загрузить доступные инструменты (скиллы + MCP)
        tools = self.get_available_tools()

        # 3. Собрать мега-промпт
        prompt = self.prompt_builder.build(
            user_message=user_message,
            memories=memories,
            tools=tools,
            conversation_history=await self.get_recent_history(limit=20)
        )

        # 4. Вызвать LLM (smart routing)
        response = await self.llm_router.complete(prompt, tools=tools)

        # 5. Если LLM запросил tool_call —执行
        while response.has_tool_calls():
            tool_results = []
            for call in response.tool_calls:
                result = await self.tool_executor.execute(call)
                tool_results.append(result)
            # Отправить результаты обратно в LLM
            response = await self.llm_router.continue_with_tools(
                prompt, tool_results
            )

        # 6. Сохранить в память (что узнали нового)
        await self.memory_manager.extract_and_store(user_message, response.text)

        # 7. Логирование
        await self.log_conversation(user_message, response)

        return response.text
```

---

## Часть 8: Roadmap с точными сроками

### Фаза 1: MVP (недели 1–3) — «Умный бот в Telegram»
| День | Задача |
|---|---|
| 1–2 | Создать проект, docker-compose (PostgreSQL + Redis), модели БД |
| 3–4 | Agent Runtime: prompt_builder + llm_router (YandexGPT) |
| 5–6 | Telegram Bot: handler message → Agent Runtime → ответ |
| 7–8 | Memory Manager: сохранение/recall через pgvector |
| 9–10 | 3 встроенных скилла: погода, напоминания, веб-поиск |
| 11–14 | Тестирование, отладка, деплой на VPS |

**Результат:** Рабочий Telegram-бот, который помнит контекст и может искать в интернете.

### Фаза 2: Скиллы + MCP (недели 4–6)
| День | Задача |
|---|---|
| 15–17 | Система скиллов: BaseSkill, загрузка, реестр |
| 18–20 | MCP-клиент: подключение к внешним MCP-серверам |
| 21–24 | WB MCP-сервер (первый микропродукт) |
| 25–28 | Ozon MCP-сервер |

**Результат:** Бот умеет работать с WB/Ozon через MCP.

### Фаза 3: Социальный слой (недели 7–10)
| День | Задача |
|---|---|
| 29–35 | FastAPI: маркетплейс скиллов (CRUD, поиск, рейтинги) |
| 36–42 | Telegram Mini App: UI маркетплейса (из PandaPal TMA) |
| 43–49 | Профили агентов, клонирование |
| 50–56 | Реферальная система, тарифы (Free/Pro) |

### Фаза 4: Масштаб (недели 11–16)
| День | Задача |
|---|---|
| 57–70 | Мульти-агент: команды агентов, делегирование |
| 71–84 | Ещё 5 MCP-серверов (1С, Битрикс24, ВК, Тинькофф, HH) |
| 85–98 | Enterprise-фичи: аудит, изоляция, SLA |
| 99–112 | Партнёрская программа, лендинг, PR |

---

## Часть 9: Ключевые выводы

| Вопрос | Ответ |
|---|---|
| Сколько стоит? | **0₽ на старте**, ~1600₽/мес в production |
| Сколько времени? | **MVP за 3 недели** |
| Нужно ли менять стек PandaPal? | **Нет** — добавляем модули, не меняем существующие |
| Что добавить к стеку? | FastAPI (для API), Playwright (для браузера), FastMCP (для MCP) |
| Главное конкурентное преимущество | **Облачный** (не self-hosted) + **социальный слой** + **русские сервисы** |
| Риски? | Стоимость YandexGPT API при масштабировании (решение: smart routing) |
