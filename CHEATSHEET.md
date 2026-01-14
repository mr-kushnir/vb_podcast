# 📋 EXAM CHEATSHEET v3.0

## 🚀 Быстрый старт
```bash
claude                           # Запуск
/project:run EXAM-42            # Полный пайплайн (30 мин)
/project:quick EXAM-42          # Быстрый режим (15 мин)
```

## 🧠 Ultrathink
```
ultrathink and [задача]         # Максимальный reasoning
```
**Когда:** архитектура, сложная отладка, security
**Не когда:** простые задачи

## 🤖 Subagents
```
@explore-agent [что искать]     # Поиск по коду
@code-reviewer [файлы]          # Ревью кода
@security-scanner               # Security аудит
@test-analyzer                  # Анализ тестов
```

**Параллельно:**
```
Launch in PARALLEL:
1. @code-reviewer: analyze src/
2. @security-scanner: check vulnerabilities
3. @test-analyzer: coverage gaps
```

**Фон:** `Ctrl+B` отправить в фон, `/tasks` просмотр

## ⌨️ Горячие клавиши
```
Shift+Tab    Auto-accept edits
Ctrl+B       Background task
Tab          Accept suggestion
/context     Показать контекст
/compact     Сжать контекст
/agents      Управление агентами
```

## 📝 Commit формат
```
test(scope): red: failing test for [what]
feat(scope): green: implement [what]
refactor(scope): improve [what]
fix(scope): resolve #123
```

## 🎯 Тайминг (30 мин)
```
0-5:   BUSINESS - BDD сценарии
5-10:  ARCHITECT - структура + ADRs
10-22: DEVELOPER - TDD циклы
22-26: QA - parallel subagents
26-30: DEPLOY - деплой + PR
```

## ⚡ Тайминг quick (15 мин)
```
0-2:   Анализ + 2-3 сценария
2-4:   Структура (без ADRs)
4-12:  TDD sprint
12-14: Quick tests + security
14-15: Deploy
```

## 📊 Context
```
40%  → Используй subagents
60%  → /compact или handoff
80%  → Обязательный handoff
```

## 🔧 YouTrack
```bash
python scripts/youtrack.py issue get EXAM-42
python scripts/youtrack.py issue state EXAM-42 "In Progress"
python scripts/youtrack.py issue state EXAM-42 "Done"
python scripts/youtrack.py kb read "Context/current-sprint.md"
python scripts/youtrack.py kb write "path" "content"
```

## 🐙 GitHub
```bash
python scripts/github_client.py issue list open "bug"
python scripts/github_client.py bug "scenario" "expected" "actual" "file"
python scripts/github_client.py security "type" "severity" "loc" "desc" "rec"
python scripts/github_client.py commit feat dev "message"
python scripts/github_client.py blockers
```

## ☁️ Deploy
```bash
./scripts/deploy.sh serverless EXAM-42
./scripts/deploy.sh container EXAM-42
./scripts/deploy.sh vm EXAM-42
```

## 🧪 Tests
```bash
pytest tests/ -v                           # Все тесты
pytest tests/ --cov=src --cov-report=term  # С coverage
pytest features/ --gherkin-terminal-reporter  # BDD
```

## 🔒 Security
```bash
bandit -r src/ -ll                # SAST
safety check                       # Dependencies
pip-audit                          # CVE check
```

---
**Удачи! 🎯**
