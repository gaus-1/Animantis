# 🔌 DEEP DIVE: Первый MCP-сервер для WB и Ozon
## Полный план: API, код, стек PandaPal, монетизация

---

## Часть 1: Что такое MCP-сервер — техническая суть

### Протокол MCP за 60 секунд

```
AI-приложение              MCP-сервер              Внешний сервис
(Claude/Cursor/            (твой код)               (WB API)
 наш агент)

     │                         │                         │
     │  1. Запрос: "Покажи     │                         │
     │     заказы за сегодня"  │                         │
     │  ───────────────────►   │                         │
     │  (JSON-RPC 2.0)         │                         │
     │                         │  2. HTTP GET             │
     │                         │  /api/v1/supplier/orders │
     │                         │  ─────────────────────►  │
     │                         │                         │
     │                         │  3. JSON response        │
     │                         │  ◄─────────────────────  │
     │                         │                         │
     │  4. Структурированный   │                         │
     │     ответ с данными     │                         │
     │  ◄───────────────────   │                         │
     │                         │                         │
```

### Три типа возможностей MCP-сервера

| Тип | Что это | Пример для WB |
|---|---|---|
| **Tools** | Функции, которые AI может **вызвать** | `get_orders()`, `reply_feedback()`, `set_price()` |
| **Resources** | Данные, которые AI может **прочитать** | `wb://daily-report`, `wb://top-products` |
| **Prompts** | Шаблоны для AI | «Проанализируй продажи за неделю и дай рекомендации» |

### Транспорт

| Режим | Когда | Как |
|---|---|---|
| **STDIO** | Локальный MCP (Claude Desktop) | stdin/stdout, JSON-RPC |
| **Streamable HTTP** | Облачный MCP (наша платформа) | HTTP + SSE, JSON-RPC |

---

## Часть 2: Wildberries API — полная карта

### Портал документации: `dev.wildberries.ru` (Swagger/OpenAPI)

### Все доступные API (группы):

| Группа API | Base URL | Что делает |
|---|---|---|
| **Контент** | `content-api.wildberries.ru` | Управление карточками товаров |
| **Цены и скидки** | `discounts-prices-api.wildberries.ru` | Установка цен, скидок |
| **Marketplace** | `marketplace-api.wildberries.ru` | Поставки, склад, FBS |
| **Статистика** | `statistics-api.wildberries.ru` | Заказы, продажи, склад |
| **Аналитика** | `seller-analytics-api.wildberries.ru` | Воронка продаж, отчёты |
| **Отзывы** | `feedbacks-api.wildberries.ru` | Чтение/ответ на отзывы |
| **Вопросы** | `questions-api.wildberries.ru` | Чтение/ответ на вопросы |
| **Рекомендации** | `recommender-api.wildberries.ru` | Рекомендации по оптимизации |
| **Рекламный кабинет** | `advert-api.wildberries.ru` | Управление рекламой |

### Ключевые эндпоинты для MCP-сервера

```
📦 ЗАКАЗЫ
├── GET  /api/v1/supplier/orders          → Список заказов (обновление: 30 мин)
├── GET  /api/v1/supplier/sales           → Список продаж
└── POST /api/v3/dbs/orders/new           → Новые заказы DBS

📊 СТАТИСТИКА
├── POST /api/analytics/v3/sales-funnel/products/history → Воронка по товарам
├── POST /api/analytics/v3/sales-funnel/grouped/history  → Сгруппированная воронка
└── GET  /api/v5/supplier/reportDetailByPeriod           → Детальный отчёт

💬 ОТЗЫВЫ
├── GET  /api/v1/feedbacks                → Список отзывов
├── POST /api/v1/feedbacks                → Ответить на отзыв
└── GET  /api/v1/feedbacks/count          → Количество без ответа

❓ ВОПРОСЫ
├── GET  /api/v1/questions                → Список вопросов
└── POST /api/v1/questions                → Ответить на вопрос

💰 ЦЕНЫ
├── POST /api/v2/list/goods/filter        → Список товаров с ценами
├── POST /api/v2/upload/task              → Массовое обновление цен
└── POST /api/v2/history/goods/size       → История цен

📦 СКЛАД
├── POST /api/v3/stocks/{warehouseId}     → Обновить остатки
└── GET  /api/v3/warehouses               → Список складов

📝 КОНТЕНТ
├── POST /content/v2/get/cards/list       → Список карточек товаров
├── POST /content/v2/cards/update         → Обновить карточку
└── GET  /content/v2/object/charcs/{subjectId} → Характеристики категории
```

### Авторизация WB API

```
Все запросы: Header "Authorization: {API_KEY}"

Типы токенов:
- Только чтение (Statistics)
- Чтение + запись (Content, Prices)
- Полный доступ
```

---

## Часть 3: Ozon Seller API — полная карта

### Портал документации: `docs.ozon.ru/api/seller/`

### Ключевые эндпоинты

```
📦 ЗАКАЗЫ / ОТПРАВЛЕНИЯ
├── POST /v3/posting/fbs/list             → Список отправлений FBS
├── POST /v3/posting/fbs/get              → Детали отправления
├── POST /v3/posting/fbs/unfulfilled/list → Невыполненные
├── POST /v2/posting/fbo/list             → Список FBO
└── POST /v3/posting/fbs/ship             → Собрать отправление

📊 АНАЛИТИКА
├── POST /v1/analytics/data               → Аналитические данные
├── POST /v1/analytics/stock_on_warehouses→ Остатки на складах
└── POST /v1/report/products/create       → Создать отчёт

💬 ОТЗЫВЫ
├── POST /v1/review/list                  → Список отзывов
└── POST /v1/review/comment/create        → Ответить на отзыв

💰 ЦЕНЫ
├── POST /v4/product/info/prices          → Получить цены
├── POST /v1/product/import/prices        → Обновить цены (до 1000 товаров)
└── POST /v2/product/info/list            → Инфо о товарах с ценами

📦 ТОВАРЫ
├── POST /v3/product/info/list            → Список товаров
├── POST /v1/product/import               → Создать/обновить товар
├── POST /v1/product/pictures/import      → Загрузить изображения
└── POST /v2/product/info/attributes      → Атрибуты товара

📦 СКЛАД
├── POST /v2/products/stocks              → Обновить остатки
└── POST /v1/product/info/stocks          → Получить остатки
```

### Авторизация Ozon API

```
Все запросы:
  Header "Client-Id: {CLIENT_ID}"
  Header "Api-Key: {API_KEY}"
```

---

## Часть 4: Реализация MCP-сервера для WB

### Полный код: `mcp-wildberries`

```python
# mcp_wildberries/server.py
"""
MCP Server для Wildberries Seller API.
pip install fastmcp httpx pydantic
"""
from fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta
from typing import Optional
import json

# Создание MCP-сервера
mcp = FastMCP(
    name="wildberries",
    description="MCP-сервер для работы с Wildberries Seller API. "
                "Управление заказами, отзывами, ценами и аналитикой."
)

# ─── Конфигурация ────────────────────────────────
WB_HEADERS = {}

def _set_auth(api_key: str) -> dict:
    """Установить API-ключ для запросов"""
    return {"Authorization": api_key}

async def _wb_request(method: str, url: str, api_key: str,
                       params: dict = None, json_data: dict = None) -> dict:
    """Универсальный HTTP-клиент для WB API с обработкой ошибок"""
    headers = _set_auth(api_key)
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers, params=params)
        else:
            response = await client.post(url, headers=headers, json=json_data)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            return {"error": "Неверный API-ключ. Проверьте токен."}
        elif response.status_code == 429:
            return {"error": "Превышен лимит запросов WB API. Подождите минуту."}
        else:
            return {
                "error": f"Ошибка WB API: {response.status_code}",
                "details": response.text[:500]
            }


# ═══════════════════════════════════════════════════
# TOOLS: Заказы
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_orders(
    api_key: str,
    date_from: str = None,
    flag: int = 0
) -> dict:
    """
    Получить список заказов из Wildberries.

    Args:
        api_key: API-ключ WB (тип: Статистика)
        date_from: Дата начала (формат: YYYY-MM-DDTHH:MM:SS, по умолчанию — вчера)
        flag: 0 — только новые (с date_from), 1 — все (с date_from)

    Returns:
        Список заказов с полями: orderId, dateCreated, warehouseName,
        nmId, sticker, totalPrice, status и др.
    """
    if not date_from:
        date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")

    return await _wb_request(
        "GET",
        "https://statistics-api.wildberries.ru/api/v1/supplier/orders",
        api_key,
        params={"dateFrom": date_from, "flag": flag}
    )


@mcp.tool()
async def get_sales(
    api_key: str,
    date_from: str = None,
    flag: int = 0
) -> dict:
    """
    Получить список продаж из Wildberries.

    Args:
        api_key: API-ключ WB (тип: Статистика)
        date_from: Дата начала (формат: YYYY-MM-DDTHH:MM:SS)
        flag: 0 — только новые, 1 — все

    Returns:
        Список продаж с полями: date, saleID, nmId, totalPrice, discountPercent и др.
    """
    if not date_from:
        date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%dT00:00:00")

    return await _wb_request(
        "GET",
        "https://statistics-api.wildberries.ru/api/v1/supplier/sales",
        api_key,
        params={"dateFrom": date_from, "flag": flag}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Отзывы
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_feedbacks(
    api_key: str,
    is_answered: bool = False,
    take: int = 50,
    skip: int = 0
) -> dict:
    """
    Получить список отзывов покупателей.

    Args:
        api_key: API-ключ WB (тип: Вопросы и отзывы)
        is_answered: True — с ответом, False — без ответа
        take: Количество (max 10000)
        skip: Пропустить N отзывов

    Returns:
        Список отзывов: id, text, productValuation, createdDate,
        productDetails (nmId, productName, supplierArticle)
    """
    return await _wb_request(
        "GET",
        "https://feedbacks-api.wildberries.ru/api/v1/feedbacks",
        api_key,
        params={"isAnswered": is_answered, "take": take, "skip": skip}
    )


@mcp.tool()
async def get_unanswered_feedbacks_count(api_key: str) -> dict:
    """
    Получить количество отзывов без ответа.

    Args:
        api_key: API-ключ WB (тип: Вопросы и отзывы)

    Returns:
        {"countUnanswered": число, "countAll": число}
    """
    return await _wb_request(
        "GET",
        "https://feedbacks-api.wildberries.ru/api/v1/feedbacks/count",
        api_key
    )


@mcp.tool()
async def reply_to_feedback(
    api_key: str,
    feedback_id: str,
    text: str
) -> dict:
    """
    Ответить на отзыв покупателя.

    Args:
        api_key: API-ключ WB (тип: Вопросы и отзывы, с правом записи)
        feedback_id: ID отзыва
        text: Текст ответа

    Returns:
        Статус операции
    """
    return await _wb_request(
        "POST",
        "https://feedbacks-api.wildberries.ru/api/v1/feedbacks",
        api_key,
        json_data={"id": feedback_id, "text": text}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Вопросы
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_questions(
    api_key: str,
    is_answered: bool = False,
    take: int = 50,
    skip: int = 0
) -> dict:
    """
    Получить список вопросов покупателей о товарах.

    Args:
        api_key: API-ключ WB (тип: Вопросы и отзывы)
        is_answered: True — с ответом, False — без ответа
        take: Количество
        skip: Пропустить

    Returns:
        Список вопросов: id, text, createdDate, productDetails
    """
    return await _wb_request(
        "GET",
        "https://questions-api.wildberries.ru/api/v1/questions",
        api_key,
        params={"isAnswered": is_answered, "take": take, "skip": skip}
    )


@mcp.tool()
async def reply_to_question(
    api_key: str,
    question_id: str,
    text: str
) -> dict:
    """
    Ответить на вопрос покупателя.

    Args:
        api_key: API-ключ WB (тип: Вопросы и отзывы, с правом записи)
        question_id: ID вопроса
        text: Текст ответа

    Returns:
        Статус операции
    """
    return await _wb_request(
        "POST",
        "https://questions-api.wildberries.ru/api/v1/questions",
        api_key,
        json_data={"id": question_id, "text": text}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Цены и скидки
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_prices(
    api_key: str,
    limit: int = 100,
    offset: int = 0
) -> dict:
    """
    Получить список товаров с текущими ценами.

    Args:
        api_key: API-ключ WB (тип: Цены и скидки)
        limit: Кол-во товаров в ответе (max 1000)
        offset: Смещение

    Returns:
        Список товаров: nmId, price, discount, promoCode
    """
    return await _wb_request(
        "POST",
        "https://discounts-prices-api.wildberries.ru/api/v2/list/goods/filter",
        api_key,
        json_data={"limit": limit, "offset": offset}
    )


@mcp.tool()
async def update_prices(
    api_key: str,
    prices: list
) -> dict:
    """
    Массовое обновление цен на товары.

    Args:
        api_key: API-ключ WB (тип: Цены и скидки, с правом записи)
        prices: Список объектов [{"nmId": 12345, "price": 1500}]

    Returns:
        Статус операции, ID задачи
    """
    return await _wb_request(
        "POST",
        "https://discounts-prices-api.wildberries.ru/api/v2/upload/task",
        api_key,
        json_data={"data": prices}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Склад
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_warehouses(api_key: str) -> dict:
    """
    Получить список складов WB для FBS.

    Args:
        api_key: API-ключ WB (тип: Marketplace)

    Returns:
        Список складов: id, name, address
    """
    return await _wb_request(
        "GET",
        "https://marketplace-api.wildberries.ru/api/v3/warehouses",
        api_key
    )


@mcp.tool()
async def update_stocks(
    api_key: str,
    warehouse_id: int,
    stocks: list
) -> dict:
    """
    Обновить остатки товаров на складе.

    Args:
        api_key: API-ключ WB (тип: Marketplace, с правом записи)
        warehouse_id: ID склада
        stocks: Список [{"sku": "артикул", "amount": 100}]

    Returns:
        Статус операции
    """
    return await _wb_request(
        "PUT",
        f"https://marketplace-api.wildberries.ru/api/v3/stocks/{warehouse_id}",
        api_key,
        json_data={"stocks": stocks}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Аналитика
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_sales_funnel(
    api_key: str,
    date_from: str,
    date_to: str,
    page: int = 1
) -> dict:
    """
    Получить воронку продаж по товарам (просмотры → корзина → заказ → выкуп).

    Args:
        api_key: API-ключ WB (тип: Аналитика)
        date_from: Начало периода (YYYY-MM-DD)
        date_to: Конец периода (YYYY-MM-DD)
        page: Номер страницы

    Returns:
        По каждому товару: openCardCount, addToCartCount,
        ordersCount, buyoutsCount, cancelCount и др.
    """
    return await _wb_request(
        "POST",
        "https://seller-analytics-api.wildberries.ru/api/analytics/v3/sales-funnel/products/history",
        api_key,
        json_data={"dateFrom": date_from, "dateTo": date_to, "page": page}
    )


# ═══════════════════════════════════════════════════
# TOOLS: Контент (карточки товаров)
# ═══════════════════════════════════════════════════

@mcp.tool()
async def get_product_cards(
    api_key: str,
    limit: int = 100,
    cursor: dict = None
) -> dict:
    """
    Получить список карточек товаров.

    Args:
        api_key: API-ключ WB (тип: Контент)
        limit: Количество (max 100)
        cursor: Курсор для пагинации (из предыдущего ответа)

    Returns:
        Список карточек: nmID, vendorCode, title,
        description, photos, sizes, characteristics
    """
    body = {"settings": {"cursor": cursor or {"limit": limit}, "filter": {"withPhoto": -1}}}
    return await _wb_request(
        "POST",
        "https://content-api.wildberries.ru/content/v2/get/cards/list",
        api_key,
        json_data=body
    )


# ═══════════════════════════════════════════════════
# RESOURCES: Готовые отчёты
# ═══════════════════════════════════════════════════

@mcp.resource("wb://help/api-tokens")
def api_tokens_guide() -> str:
    """Инструкция: как получить API-ключ Wildberries"""
    return """
    # Как получить API-ключ Wildberries

    1. Зайти в ЛК продавца → Настройки → Доступ к API
    2. Нажать «Создать ключ»
    3. Выбрать категории доступа:
       - Статистика — для заказов и продаж
       - Контент — для карточек товаров
       - Цены и скидки — для управления ценами
       - Вопросы и отзывы — для обратной связи
       - Marketplace — для FBS/FBO
       - Аналитика — для воронки и отчётов
    4. Скопировать ключ (показывается ОДИН раз!)

    Формат: строка вида "eyJhbGciOiJFUzI1NiIsIn..."
    """


# ═══════════════════════════════════════════════════
# PROMPTS: Готовые сценарии
# ═══════════════════════════════════════════════════

@mcp.prompt()
def daily_report_prompt() -> str:
    """Промпт для ежедневного отчёта продавца WB"""
    return """
    Сделай ежедневный отчёт по моему магазину на Wildberries:

    1. Получи заказы за сегодня (get_orders)
    2. Получи продажи за сегодня (get_sales)
    3. Проверь количество неотвеченных отзывов (get_unanswered_feedbacks_count)
    4. Получи воронку продаж за последние 7 дней (get_sales_funnel)

    Сформируй краткий отчёт в формате:
    📊 Отчёт за [дата]
    • Заказов: X (на сумму Y₽)
    • Продаж: X (на сумму Y₽)
    • Неотвеченных отзывов: X
    • Конверсия просмотр→заказ: X%

    Если есть критические моменты (резкое падение заказов,
    много негативных отзывов) — укажи отдельно.
    """


@mcp.prompt()
def auto_reply_feedbacks_prompt() -> str:
    """Промпт для автоответов на отзывы"""
    return """
    Помоги ответить на отзывы покупателей:

    1. Получи неотвеченные отзывы (get_feedbacks с is_answered=False)
    2. Для каждого отзыва:
       - Если оценка 4-5: поблагодари за покупку
       - Если оценка 1-3: извинись, предложи решение
       - Используй вежливый, профессиональный тон
       - Упомяни конкретные детали из отзыва
    3. Покажи мне ответы для проверки перед отправкой
    4. После моего одобрения — отправь (reply_to_feedback)
    """


# ═══════════════════════════════════════════════════
# Запуск
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
```

---

## Часть 5: Структура проекта MCP-сервера

```
mcp-wildberries/
├── mcp_wildberries/
│   ├── __init__.py
│   ├── server.py              # Главный файл MCP-сервера (код выше)
│   ├── wb_client.py           # HTTP-клиент для WB API (отдельно для тестов)
│   └── models.py              # Pydantic-модели для валидации
│
├── tests/
│   ├── test_tools.py          # Unit-тесты для каждого tool
│   ├── test_wb_client.py      # Тесты HTTP-клиента (mock)
│   └── conftest.py            # pytest fixtures
│
├── pyproject.toml             # Метаданные пакета
├── README.md                  # Документация на русском + английском
├── LICENSE                    # MIT License
└── .github/
    └── workflows/
        └── publish.yml        # Auto-publish на PyPI при release

# pyproject.toml
[project]
name = "mcp-wildberries"
version = "0.1.0"
description = "MCP server for Wildberries Seller API"
dependencies = ["fastmcp>=2.0", "httpx>=0.27", "pydantic>=2.0"]

[project.scripts]
mcp-wildberries = "mcp_wildberries.server:mcp.run"
```

---

## Часть 6: Как подключить к стеку PandaPal

### Вариант 1: Как MCP-сервер (отдельный процесс)

```python
# В Agent Runtime (agent/runtime.py) подключаем MCP-клиент:
from fastmcp import Client

async def connect_wb_mcp():
    """Подключиться к WB MCP-серверу"""
    client = Client("mcp-wildberries")
    async with client:
        # Получить список доступных tools
        tools = await client.list_tools()
        # Вызвать tool
        result = await client.call_tool(
            "get_orders",
            {"api_key": user.wb_api_key, "date_from": "2026-03-13T00:00:00"}
        )
        return result
```

### Вариант 2: Как Python-модуль (внутри PandaPal)

```python
# Прямой импорт без MCP-протокола (быстрее)
from mcp_wildberries.wb_client import WBClient

async def get_wb_orders(user):
    client = WBClient(api_key=user.wb_api_key)
    orders = await client.get_orders(date_from="2026-03-13")
    return orders
```

### Что добавить в PandaPal для интеграции

| Файл | Изменение |
|---|---|
| `requirements.txt` | Добавить: `fastmcp>=2.0`, `httpx>=0.27` |
| `config/settings.py` | Добавить: `WB_MCP_ENABLED`, `OZON_MCP_ENABLED` |
| `agent/runtime.py` | Добавить MCP-клиент в Tool Executor |
| `db/models.py` | Добавить поле `mcp_configs` в модель User/Agent |
| `bot/handlers/` | Добавить хэндлер `/connect_wb` для привязки API-ключа |

---

## Часть 7: Стоимость создания MCP-сервера

| Статья | Стоимость |
|---|---|
| Python + FastMCP | **0₽** (open source) |
| httpx (HTTP-клиент) | **0₽** (open source) |
| WB API доступ | **0₽** (бесплатный для продавцов) |
| PyPI публикация | **0₽** |
| mcp.so публикация | **0₽** |
| GitHub репозиторий | **0₽** |
| Время разработки | **2–3 дня** |
| **ИТОГО** | **0₽** |

### Стоимость для Ozon MCP-сервера

Абсолютно аналогично — **0₽**, ещё 2–3 дня разработки. Структура кода та же, меняются только URL-адреса API и формат авторизации (Client-Id + Api-Key вместо одного Authorization).

---

## Часть 8: Монетизация MCP-серверов

### Стратегия Open-Core

```
FREE (GitHub / PyPI / mcp.so):                 PRO ($9.99/мес):
├── get_orders                                  ├── Всё из Free +
├── get_sales                                   ├── get_sales_funnel
├── get_feedbacks                               ├── auto_reply_feedbacks (AI)
├── get_prices                                  ├── competitor_analysis
├── get_warehouses                              ├── price_optimization
└── reply_to_feedback                           ├── seo_card_optimizer
                                                 ├── daily_report_scheduled
                                                 ├── stock_forecast
                                                 └── priority support
```

### Где размещать и продавать

| Платформа | Бесплатная версия | Pro версия | Как |
|---|---|---|---|
| **PyPI** | ✅ `pip install mcp-wildberries` | ❌ | Open source |
| **mcp.so** | ✅ Листинг | ❌ | Публикация |
| **GitHub** | ✅ Код | ❌ | Open source |
| **Свой сайт** | ✅ Базовый | ✅ Pro | Stripe/ЮKassa |
| **Telegram Bot** | ✅ Базовый | ✅ Pro | Telegram Payments / Stars |
| **Apify** | ✅ + ✅ | ✅ | 70% от продаж тебе |

---

## Часть 9: План создания — день за днём

### MCP Wildberries (5 дней)

| День | Задачи | Результат |
|---|---|---|
| **День 1** | Изучить dev.wildberries.ru, попробовать API в Postman | Понимание всех эндпоинтов |
| **День 2** | Написать `wb_client.py` (HTTP-клиент) + тесты | Рабочий клиент для WB API |
| **День 3** | Написать `server.py` (MCP tools/resources/prompts) | 12+ tools |
| **День 4** | Тесты, README, pyproject.toml | Готов к публикации |
| **День 5** | Публикация: PyPI + mcp.so + GitHub + статья на vc.ru | Первые юзеры |

### MCP Ozon (3 дня — после WB)

| День | Задачи | Результат |
|---|---|---|
| **День 6** | Адаптировать wb_client.py → ozon_client.py | HTTP-клиент для Ozon |
| **День 7** | Написать `server.py` для Ozon (аналогично WB) | 10+ tools |
| **День 8** | Тесты, README, публикация | Оба МСР-сервера в продакшне |

### Бандл «E-commerce» (2 дня)

| День | Задачи | Результат |
|---|---|---|
| **День 9** | Объединить WB + Ozon в один пакет | `mcp-ecommerce-ru` |
| **День 10** | Лендинг, Telegram-канал, посты в чатах продавцов | Маркетинг-машина запущена |

---

## Часть 10: Итоговая таблица

| Параметр | MCP Wildberries | MCP Ozon |
|---|---|---|
| **Стоимость разработки** | 0₽ | 0₽ |
| **Время разработки** | 5 дней | 3 дня |
| **Стек** | Python, FastMCP, httpx | Тот же |
| **Совместимость с PandaPal** | 100% | 100% |
| **Что менять в PandaPal** | Ничего (отдельный пакет) | Ничего |
| **Что ДОБАВИТЬ** | fastmcp, httpx в requirements | Те же |
| **Публикация** | PyPI + mcp.so + GitHub | Те же |
| **Конкуренты** | 0 | 0 |
| **Потенциальные юзеры** | 500 000+ | 300 000+ |
| **Монетизация** | Free + Pro ($9.99/мес) | Free + Pro ($9.99/мес) |
