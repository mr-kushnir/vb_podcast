# 🚀 Multi-Agent Exam System v3.0

**Автономная система разработки с последними возможностями Claude Code (январь 2026)**

## ✨ Что нового в v3.0

| Функция | Описание |
|---------|----------|
| **Ultrathink** | Максимальный reasoning для сложных задач |
| **Custom Subagents** | Изолированные агенты для параллельной работы |
| **Skills** | Auto-discovery паттернов и шаблонов |
| **Hooks** | Автоматические quality gates |
| **Plan Mode + Revving** | Итеративное улучшение планов |
| **Async Execution** | Фоновые задачи без блокировки |

---

## 📦 Структура проекта

```
exam-v3/
├── CLAUDE.md                      # Главные инструкции (читать!)
├── .env.example                   # Шаблон переменных окружения
│
├── .claude/
│   ├── settings.json              # Hooks + permissions
│   │
│   ├── agents/                    # Custom subagents
│   │   ├── code-reviewer.md       # Ревью кода
│   │   ├── security-scanner.md    # Security аудит
│   │   └── test-analyzer.md       # Анализ тестов
│   │
│   ├── commands/                  # Slash commands
│   │   ├── run.md                 # /project:run - полный пайплайн
│   │   └── quick.md               # /project:quick - быстрый режим
│   │
│   └── skills/                    # Auto-discovered skills
│       ├── bdd-testing/
│       │   └── SKILL.md           # BDD/Gherkin паттерны
│       └── tdd-workflow/
│           └── SKILL.md           # TDD Red-Green-Refactor
│
├── scripts/
│   ├── youtrack.py                # YouTrack API клиент
│   ├── github_client.py           # GitHub API клиент
│   ├── deploy.sh                  # Деплой в Yandex Cloud
│   │
│   ├── session_init.py            # Hook: старт сессии
│   ├── auto_lint.py               # Hook: автолинт
│   ├── security_gate.py           # Hook: security проверка
│   ├── test_watcher.py            # Hook: мониторинг тестов
│   └── auto_commit.py             # Hook: автокоммит
│
├── features/                      # BDD сценарии
├── src/                           # Исходный код
├── tests/                         # Тесты
├── docs/                          # Документация
└── logs/                          # Логи агентов
```

---

## ⚡ Быстрый старт

### 1. Установка
```bash
# Распаковать архив
unzip exam-v3.zip && cd exam-v3

# Сделать скрипты исполняемыми
chmod +x scripts/*.sh scripts/*.py
```

### 2. Настройка .env
```bash
cp .env.example .env
nano .env  # Заполнить все переменные
```

**Необходимые переменные:**
```bash
# YouTrack
YOUTRACK_URL=https://your-org.youtrack.cloud
YOUTRACK_TOKEN=perm:xxx
YOUTRACK_PROJECT=EXAM

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=username/repo

# Yandex Cloud
YC_TOKEN=y0_xxx
YC_FOLDER_ID=xxx

# App
BOT_TOKEN=xxx  # Если Telegram бот
```

### 3. Запуск
```bash
# Запустить Claude Code
claude

# Полный пайплайн (30 мин)
/project:run EXAM-42

# Быстрый режим (15 мин)
/project:quick EXAM-42
```

---

## 🧠 Ultrathink Mode

### Что это
Расширенный режим reasoning с максимальным бюджетом токенов (~32k) для глубокого анализа.

### Как использовать
```
ultrathink and analyze the requirements for user authentication
```

**Важно**: Только слово `ultrathink` работает в v2.0+. Старые keywords (`think hard`, `think harder`) отключены.

### Когда применять
- ✅ Архитектурные решения
- ✅ Сложная отладка
- ✅ Security анализ
- ✅ Оптимизация производительности
- ❌ Простые задачи (трата токенов)

### Revving (итеративное улучшение)
```
1. "ultrathink and create a plan for [task]"
2. "Critique this plan - what's missing?"
3. "Revise based on critique"
4. "Execute final plan"
```

---

## 🤖 Subagents (параллельные агенты)

### Встроенные агенты
| Агент | Модель | Назначение |
|-------|--------|------------|
| `@explore-agent` | Haiku | Поиск по файлам (быстрый) |
| `@task-agent` | Sonnet | Общие задачи |

### Кастомные агенты (в .claude/agents/)
| Агент | Назначение |
|-------|------------|
| `@code-reviewer` | Ревью кода, SOLID, best practices |
| `@security-scanner` | SAST, dependency check, CVE |
| `@test-analyzer` | Coverage, test quality, gaps |

### Параллельный запуск
```
Launch these subagents IN PARALLEL:
1. @code-reviewer: analyze src/handlers/
2. @security-scanner: scan for vulnerabilities
3. @test-analyzer: check coverage gaps

Synthesize findings when all complete.
```

### Async выполнение
```
Ctrl+B  → Отправить в фон
/tasks  → Просмотр фоновых задач
```

---

## 📚 Skills (автоматические паттерны)

### Как работают
1. Claude сканирует описания skills при старте задачи
2. Сопоставляет с текущим контекстом
3. Автоматически загружает релевантные skills
4. Применяет шаблоны и паттерны

### Включённые skills
| Skill | Триггеры |
|-------|----------|
| `bdd-testing` | "tests", "features", "Gherkin", "BDD" |
| `tdd-workflow` | "implement", "code", "TDD", "red-green" |

### Пример автоактивации
```
User: "Create tests for user registration"
→ Claude автоматически загружает bdd-testing skill
→ Применяет Gherkin шаблоны
```

---

## 🔗 Hooks (автоматизация)

### Настроенные hooks

| Event | Trigger | Action |
|-------|---------|--------|
| `SessionStart` | Старт Claude | Sync YouTrack KB |
| `PostToolUse(Write)` | После записи файла | Auto-lint |
| `PostToolUse(Bash *test*)` | После тестов | Log results |
| `PreToolUse(Bash)` | Перед bash | Security check |
| `Stop` | Конец ответа | Auto-commit |

### Как это работает
```json
// .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {"type": "command", "command": "python scripts/auto_lint.py"}
        ]
      }
    ]
  }
}
```

---

## 🎯 Workflow: Полный пайплайн

### Фаза 1: BUSINESS (ultrathink)
```
ultrathink → BDD сценарии → YouTrack KB update → commit
```

### Фаза 2: ARCHITECT (plan mode)
```
plan mode → ADRs → patterns → project structure → commit
```

### Фаза 3: DEVELOPER (TDD)
```
For each scenario:
  RED → commit → GREEN → commit → REFACTOR → commit
```

### Фаза 4: QA (parallel subagents)
```
Launch parallel:
  @test-analyzer + @security-scanner + @code-reviewer
Synthesize → GitHub issues
```

### Фаза 5: DEPLOYER
```
Check blockers → deploy → health check → PR → YouTrack Done
```

---

## 📊 Context Management

### Мониторинг
```
/context  → Визуализация контекста
/stats    → Статистика сессии
```

### Стратегия
| Usage | Action |
|-------|--------|
| 40% | Начать использовать subagents |
| 60% | Compact или handoff |
| 80% | Обязательный handoff |

### Оптимизация
- Subagents для exploration (не засоряют контекст)
- Skills с progressive disclosure
- @ references вместо paste
- Удалять неиспользуемые MCP серверы

---

## 🔑 Получение токенов

### YouTrack
1. Profile → Account Security → Tokens
2. New token → YouTrack scope (Read, Write)
3. Скопировать в `YOUTRACK_TOKEN`

### GitHub
1. Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Scopes: `repo`, `workflow`
4. Скопировать в `GITHUB_TOKEN`

### Yandex Cloud
1. https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb
2. Авторизоваться
3. Скопировать токен в `YC_TOKEN`
4. Cloud ID и Folder ID из консоли

---

## ⚠️ Checklist перед экзаменом

- [ ] `.env` заполнен и проверен
- [ ] YouTrack доступен, тестовая задача создана
- [ ] GitHub репозиторий создан и доступен
- [ ] Yandex Cloud настроен (yc config list)
- [ ] Claude Code обновлён (`claude --version` → 2.1+)
- [ ] Тестовый запуск `/project:quick TEST-1` прошёл
- [ ] Skills и subagents загружаются (`/agents`, `/context`)

---

## 🚀 Команды

| Команда | Описание | Время |
|---------|----------|-------|
| `/project:run TASK` | Полный пайплайн | ~30 мин |
| `/project:quick TASK` | Быстрый режим | ~15 мин |
| `/context` | Показать контекст | - |
| `/agents` | Управление subagents | - |
| `/compact` | Сжать контекст | - |

---

## 💡 Pro Tips

1. **Ultrathink экономно** — дорого в токенах
2. **Subagents для exploration** — держит контекст чистым  
3. **Commit часто** — не потеряете работу
4. **Hooks работают автоматически** — доверяйте им
5. **Skills активируются сами** — просто пишите задачу

---

**Удачи на экзамене! 🎯**
