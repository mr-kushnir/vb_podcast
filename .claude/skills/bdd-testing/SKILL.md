---
description: "BDD testing with Gherkin scenarios. ACTIVATE for: writing tests, creating features, behavior specs, acceptance criteria, test-first development, pytest-bdd"
allowed-tools: Task, Read, Write, Bash
---

# BDD Testing Skill

## When This Skill Activates
- Creating new features
- Writing acceptance criteria
- Test-first development
- Gherkin scenario creation
- pytest-bdd workflows

## Gherkin Template

```gherkin
Feature: [Feature Name]
  As a [role]
  I want [capability]
  So that [benefit]

  Background:
    Given [common precondition]

  @happy-path @smoke
  Scenario: [Main success scenario]
    Given [initial context]
    And [additional context]
    When [action]
    And [additional action]
    Then [expected outcome]
    And [additional verification]

  @edge-case
  Scenario: [Boundary condition handling]
    Given [edge condition setup]
    When [action]
    Then [appropriate response]

  @error-handling @negative
  Scenario: [Error scenario]
    Given [error condition]
    When [action]
    Then [error is handled gracefully]
    And [user receives meaningful feedback]

  @validation
  Scenario Outline: [Validation rules]
    Given I have input "<input>"
    When I submit the form
    Then I should see "<result>"

    Examples:
      | input       | result  |
      | valid_data  | success |
      | empty       | error   |
      | invalid     | error   |
```

## Step Definition Template

```python
# tests/step_defs/test_[feature]_steps.py
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load all scenarios from feature file
scenarios('../features/[feature].feature')

# Fixtures
@pytest.fixture
def context():
    return {}

# Given steps
@given('[precondition text]')
def given_precondition(context):
    # Setup code
    context['setup'] = True

@given(parsers.parse('I have input "{input}"'))
def given_input(context, input):
    context['input'] = input

# When steps  
@when('[action text]')
def when_action(context):
    # Action code
    context['result'] = perform_action(context['input'])

# Then steps
@then('[expected outcome]')
def then_outcome(context):
    assert context['result'] == expected_value

@then(parsers.parse('I should see "{message}"'))
def then_message(context, message):
    assert message in context['response']
```

## Tags Convention
- `@happy-path` - Main success scenarios
- `@edge-case` - Boundary conditions
- `@error-handling` - Error scenarios
- `@negative` - Invalid input tests
- `@smoke` - Quick verification tests
- `@slow` - Long-running tests
- `@wip` - Work in progress

## Running BDD Tests

```bash
# Run all BDD tests
pytest features/ -v --gherkin-terminal-reporter

# Run specific tag
pytest features/ -v -m "happy_path"

# Run specific feature
pytest features/[name].feature -v

# With coverage
pytest features/ --cov=src --cov-report=term-missing
```

## Best Practices
1. One scenario = one behavior
2. Keep scenarios independent
3. Use Background for common setup
4. Scenario Outline for data-driven tests
5. Tags for filtering and organization
6. Business language, not technical
