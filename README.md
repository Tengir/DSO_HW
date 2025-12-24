# DSO Course Project

Этот репозиторий используется для выполнения практических заданий по курсу безопасной разработки ПО.
Мы реализуем сервис интервальных повторений “Learning Flashcards”. Сейчас фокус на MVP по требованиям курса: регистрация, логин, роли и CRUD по колодам с owner-only доступом.

## Установка

Перед началом работы рекомендуется создать виртуальное окружение:

```
python -m venv .venv
```

Активация:

Windows:
```
.venv\Scripts\activate
```

Linux/macOS:
```
source .venv/bin/activate
```

Установка зависимостей:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## CI

В репозитории настроен workflow CI (GitHub Actions) — required check для main.

CI выполняет следующие проверки:

1. **Линтеры и форматтеры**: ruff, black, isort
2. **Проверка безопасности**: bandit (сканирование кода на уязвимости)
3. **Тесты с coverage**: pytest с проверкой покрытия ≥ 80%
4. **Pre-commit hooks**: все проверки из `.pre-commit-config.yaml`

Если coverage ниже 80%, CI блокирует merge в main.

Badge добавится автоматически после загрузки шаблона в GitHub.

## Контейнеризация (P07)

Сборка образа:
```
docker build -t dso-app:local .
```

Запуск контейнера:
```
docker run --rm -p 8000:8000 dso-app:local
```

Запуск через compose:
```
docker compose -f docker-compose.yml up --build
```

Проверка healthcheck:
```
curl http://localhost:8000/health
```

Линтер Dockerfile (hadolint):
```
docker run --rm -i hadolint/hadolint < Dockerfile
```

## Запуск приложения

Минимальный MVP уже реализован. Запуск локально:

```
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Настройки (env)

```
APP_ADMIN_EMAIL=admin@example.com
APP_CORS_ORIGINS=http://localhost:3000
```

### Быстрый пример (auth + колоды)

1) Регистрация:
```
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123","locale":"ru","proficiency_level":"b1"}'
```

2) Логин (получить токен):
```
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Password123"}'
```

3) Создать колоду:
```
curl -X POST http://127.0.0.1:8000/api/v1/decks \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My deck","description":"Basics","source_lang":"en","target_lang":"ru"}'
```

Если email совпадает с `APP_ADMIN_EMAIL`, пользователь регистрируется с ролью `admin`.

### API docs

Swagger UI:
```
http://127.0.0.1:8000/docs
```

ReDoc:
```
http://127.0.0.1:8000/redoc
```

## Тесты

Тесты находятся в каталоге `tests/`.

### Базовый запуск

```
pytest -q
```

### Запуск с coverage

```
pytest --cov=app --cov-report=term-missing --cov-report=html
```

После запуска отчёт будет в `htmlcov/index.html`. Coverage должен быть ≥ 80%.

### Запуск конкретных тестов

```
pytest tests/test_secure_upload.py -v
pytest tests/test_rfc7807_errors.py -v
```

## Линтеры и проверки стиля

В проекте используются ruff, black, isort, bandit и pre-commit.

### Основные команды

```bash
# Проверка стиля кода
ruff check .
black --check .
isort --check-only .

# Исправление стиля
ruff check --fix .
black .
isort .

# Проверка безопасности (bandit)
bandit -r app/ -ll

# Запуск всех проверок pre-commit
pre-commit run --all-files
```

### Проверка безопасности

Bandit проверяет код на типичные уязвимости безопасности:

```bash
bandit -r app/ -ll
```

Для более детального отчёта:

```bash
bandit -r app/ -f json -o bandit-report.json
```

Перед коммитами рекомендуется запускать `pre-commit run --all-files` локально.

## Структура проекта

```
app/                    исходный код приложения
  ├── main.py          FastAPI приложение, endpoints
  ├── schemas.py       Pydantic-схемы API
  ├── domain/          доменные модели
  ├── services/        бизнес-логика (use-cases)
  ├── adapters/        репозитории (in-memory)
  ├── shared/          общие утилиты/ошибки
  ├── config.py        Конфигурация (секреты, настройки)
  ├── errors.py        Обработка ошибок (RFC 7807, correlation_id, маскирование PII)
  └── secure_upload.py Безопасная загрузка файлов (magic bytes, path traversal защита)
tests/                  тесты
  ├── test_auth.py            тесты регистрации/логина
  ├── test_decks.py           тесты CRUD и owner-only
  ├── test_secure_upload.py    тесты безопасной загрузки файлов
  ├── test_rfc7807_errors.py   тесты формата ошибок
  ├── test_errors.py           тесты валидации и ошибок
  ├── test_config.py           тесты конфигурации
  └── test_health.py            тесты health endpoint
docs/                   документация
  ├── adr/             архитектурные решения
  ├── security-nfr/    NFR по безопасности
  └── threat-model/    модель угроз (STRIDE, RISKS, DFD)
.github/               конфигурации CI
requirements.txt       основные зависимости
requirements-dev.txt  зависимости для разработки
pyproject.toml        конфигурация инструментов (ruff, bandit, coverage)
.pre-commit-config.yaml  pre-commit hooks
Dockerfile
compose.yaml
```

## Работа с проектом

### Первый запуск

1. Создайте виртуальное окружение:
   ```bash
   python -m venv .venv
   ```

2. Активируйте окружение:
   ```bash
   # Windows
   .venv\Scripts\activate
   # Linux/macOS
   source .venv/bin/activate
   ```

3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. Настройте pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Типичный workflow

1. **Перед началом работы**: убедитесь, что все тесты проходят:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

2. **Во время разработки**: запускайте тесты для изменённых модулей:
   ```bash
   pytest tests/test_secure_upload.py -v
   ```

3. **Перед коммитом**: запустите все проверки:
   ```bash
   pre-commit run --all-files
   ```

4. **Проверка безопасности**: периодически запускайте bandit:
   ```bash
   bandit -r app/ -ll
   ```

### Покрытие тестами

Текущее покрытие можно проверить:

```bash
pytest --cov=app --cov-report=term-missing --cov-report=html
```

Открыть HTML отчёт:
```bash
# Windows
start htmlcov/index.html
# Linux/macOS
open htmlcov/index.html
```

Минимальное покрытие для проекта: **80%**.

## Дополнительно

- Для конфигурации используется файл `.env` (пример — `.env.example`).
- Секреты и персональные данные в репозиторий не добавляются.
- Политика безопасности описана в файле `SECURITY.md`.
- Все секреты маскируются в логах и строковых представлениях (см. `app/config.py`).
- Ошибки возвращаются в формате RFC 7807 с `correlation_id` для трейсабельности.
