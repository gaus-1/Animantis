# Animantis — Первоначальная настройка Railway

## Что сделать ПРЯМО СЕЙЧАС

### Шаг 1: Создать проект Railway

1. Зайти на [railway.app](https://railway.app)
2. **New Project** → **Empty Project**
3. Назвать: **animantis**

### Шаг 2: Добавить PostgreSQL

1. В проекте: **+ New** → **Database** → **Add PostgreSQL**
2. Railway создаст инстанс автоматически
3. Перейти в PostgreSQL сервис → **Variables** → скопировать `DATABASE_URL`
4. **Включить pgvector:**
   - Перейти в PostgreSQL → **Data** → **Query**
   - Выполнить:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   - Проверить:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

### Шаг 3: Добавить Redis

1. **+ New** → **Database** → **Add Redis**
2. Railway создаст автоматически
3. Скопировать `REDIS_URL` из Variables

### Шаг 4: Записать переменные

Пока что записать себе (понадобятся при деплое кода):

```
DATABASE_URL=<из Railway PostgreSQL>
REDIS_URL=<из Railway Redis>
TELEGRAM_BOT_TOKEN=<от @BotFather для @AnimantisBot>
YANDEX_API_KEY=<тот же что у PandaPal>
YANDEX_FOLDER_ID=<тот же что у PandaPal>
```

### Шаг 5: Домен

1. В будущем сервисе `frontend` → **Settings** → **Domains**
2. **+ Custom Domain** → `animantis.ru`
3. Railway покажет DNS-записи — прописать у регистратора:
   - **CNAME**: `@` → `<значение от Railway>`
   - Или **A-запись** если показали IP

---

## В pgAdmin (если хочешь подключиться локально)

### Подключение к Railway PostgreSQL

1. В Railway: PostgreSQL → **Connect** → **Connection Info**
2. Скопировать:
   - Host: `<xxx>.railway.app`
   - Port: `<порт>`
   - Database: `railway`
   - Username: `postgres`
   - Password: `<пароль>`
3. В pgAdmin: **Add New Server**
   - Name: `Animantis Railway`
   - Connection:
     - Host: из Railway
     - Port: из Railway
     - Database: `railway`
     - Username: `postgres`
     - Password: из Railway
   - SSL: **Require** (обязательно!)

### Начальные SQL (выполнить в pgAdmin или Railway Query)

```sql
-- 1. Включить pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Создать базовые таблицы (позже заменит Alembic, но для теста)
-- Пока НЕ создавай таблицы вручную — это сделает Alembic при первом деплое
-- Эта секция только для проверки что БД работает:
SELECT version();
SELECT * FROM pg_extension;
```

---

## Итого: что будет в Railway после настройки

```
Railway Project: animantis
├── PostgreSQL  ✅ (с pgvector)
├── Redis       ✅
├── api         ⏳ (создастся при первом деплое кода)
├── worker      ⏳
├── beat        ⏳
└── frontend    ⏳
```

**Первые 3 сервиса (api, worker, beat, frontend) создадутся когда будет код.**
Сейчас нужно только PostgreSQL + Redis + записать переменные.
