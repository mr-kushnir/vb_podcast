---
description: "TDD (Test-Driven Development) workflow. ACTIVATE for: writing code, implementing features, red-green-refactor, test-first coding, implementation tasks"
allowed-tools: Task, Read, Write, Bash
---

# TDD Workflow Skill

## When This Skill Activates
- Implementing new features
- Writing production code
- Red-green-refactor cycles
- Test-first development

## TDD Cycle

```
┌─────────────────────────────────────────────────┐
│                   TDD CYCLE                      │
│                                                  │
│    ┌───────┐      ┌───────┐      ┌──────────┐  │
│    │  RED  │ ───▶ │ GREEN │ ───▶ │ REFACTOR │  │
│    │       │      │       │      │          │  │
│    │ Write │      │ Make  │      │ Improve  │  │
│    │ test  │      │ pass  │      │ code     │  │
│    └───────┘      └───────┘      └──────────┘  │
│        ▲                              │        │
│        └──────────────────────────────┘        │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Phase 1: RED (Write Failing Test)

```python
# tests/test_[feature].py
def test_[scenario_name]():
    """
    BDD: [Scenario from .feature file]
    Expected: [What should happen]
    """
    # Arrange
    input_data = {"name": "test"}
    
    # Act
    result = function_under_test(input_data)
    
    # Assert
    assert result["status"] == "success"
    assert "id" in result
```

**Commit:**
```bash
git add tests/
git commit -m "test(scope): red: add failing test for [scenario]

Expected behavior: [description]
Currently fails because: function not implemented"
```

## Phase 2: GREEN (Make Test Pass)

Write MINIMAL code to pass:
```python
# src/[module].py
def function_under_test(input_data):
    # Simplest implementation that passes
    return {
        "status": "success",
        "id": 1
    }
```

**Verify:**
```bash
pytest tests/test_[feature].py -v
```

**Commit:**
```bash
git add src/
git commit -m "feat(scope): green: implement [scenario]

- Minimal implementation to pass test
- [What was added]

TDD Phase: GREEN"
```

## Phase 3: REFACTOR (Improve Code)

Improve without breaking tests:
```python
# Better implementation
def function_under_test(input_data):
    validated = validate_input(input_data)
    result = process(validated)
    return {
        "status": "success",
        "id": result.id,
        "created_at": result.created_at
    }
```

**Verify:**
```bash
pytest tests/ -v  # ALL tests still pass
```

**Commit:**
```bash
git add .
git commit -m "refactor(scope): improve [component]

- [What was improved]
- [Why it's better]
- All tests still passing

TDD Phase: REFACTOR"
```

## Commit Frequency

| Phase | Commit? | Message Format |
|-------|---------|----------------|
| RED | ✅ Yes | `test(scope): red: [what]` |
| GREEN | ✅ Yes | `feat(scope): green: [what]` |
| REFACTOR | ✅ Yes | `refactor(scope): [what]` |

**Target: 3 commits per TDD cycle**

## Test Structure (AAA)

```python
def test_something():
    # Arrange - Setup
    user = create_test_user()
    input_data = {"user_id": user.id}
    
    # Act - Execute
    result = service.process(input_data)
    
    # Assert - Verify
    assert result.success is True
    assert result.data["user_id"] == user.id
```

## Test Naming Convention

```python
def test_[unit]_[scenario]_[expected]:
    pass

# Examples:
def test_user_registration_with_valid_email_succeeds():
def test_user_registration_with_duplicate_email_fails():
def test_payment_processing_with_insufficient_funds_returns_error():
```

## Rules
1. NEVER skip RED phase
2. Write test BEFORE implementation
3. One test = one behavior
4. Tests must be able to fail
5. Commit after each phase
6. Run ALL tests before refactor commit
