Execute full autonomous BDD/TDD pipeline with ultrathink and parallel subagents.

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS PIPELINE v3.0                              │
│                                                                          │
│  YouTrack ──▶ BUSINESS ──▶ ARCHITECT ──▶ DEVELOPER ──▶ QA ──▶ DEPLOY   │
│     │        (ultrathink)  (plan mode)    (TDD)      (parallel)         │
│     │             │             │            │            │              │
│     ▼             ▼             ▼            ▼            ▼              │
│  Read task   BDD specs      ADRs        Code+Tests   TESTER+SECURITY   │
│  Update KB   Gherkin        Patterns    Commits      GitHub Issues      │
└─────────────────────────────────────────────────────────────────────────┘
```

## Execution Steps

### Phase 1: Task Analysis (BUSINESS - ultrathink)

```
ultrathink and analyze the task requirements:

1. Read task from YouTrack:
   python scripts/youtrack.py issue get $TASK_ID

2. Update status to In Progress:
   python scripts/youtrack.py issue state $TASK_ID "In Progress"

3. Create comprehensive BDD scenarios in Gherkin format
   - Cover ALL acceptance criteria
   - Include happy path, edge cases, error handling
   - Use Scenario Outline for data-driven tests

4. Save to features/[feature].feature

5. Update Knowledge Base:
   python scripts/youtrack.py kb write "Context/current-sprint.md" "[context]"

6. Commit:
   git add features/ && git commit -m "feat(business): BDD scenarios for $TASK_ID"
```

### Phase 2: Architecture (ARCHITECT - plan mode)

```
Enter plan mode and design the solution:

1. Read BDD scenarios and KB context

2. ultrathink about architecture:
   - Tech stack selection
   - Design patterns
   - Component structure
   - API contracts

3. Create Architecture Decision Records (ADRs)

4. Document in KB:
   python scripts/youtrack.py kb write "Architecture/decisions.md" "[ADRs]"
   python scripts/youtrack.py kb write "Architecture/patterns.md" "[patterns]"

5. Create project structure

6. Commit:
   git commit -m "docs(architect): architecture decisions for $TASK_ID"
```

### Phase 3: Implementation (DEVELOPER - TDD)

```
For each BDD scenario, execute TDD cycle:

1. RED: Write failing test
   git commit -m "test(dev): red: failing test for [scenario]"

2. GREEN: Implement minimal code
   git commit -m "feat(dev): green: implement [scenario]"

3. REFACTOR: Improve code quality
   git commit -m "refactor(dev): improve [component]"

4. Check for open GitHub issues and fix them:
   python scripts/github_client.py issue list open "bug,security"

5. Push changes:
   git push origin $(git branch --show-current)
```

### Phase 4: Quality Assurance (PARALLEL SUBAGENTS)

```
Launch these subagents IN PARALLEL:

1. @test-analyzer:
   - Run all tests with coverage
   - Identify coverage gaps
   - Create issues for failures

2. @security-scanner:
   - Run SAST (bandit, safety)
   - Check dependencies
   - Create security issues

3. @code-reviewer:
   - Review code quality
   - Check SOLID principles
   - Identify improvements

Wait for all to complete, then synthesize findings.

If CRITICAL issues found:
- Create GitHub issues
- Update KB blockers
- Notify about deployment block
```

### Phase 5: Deployment (DEPLOYER)

```
1. Check for blockers:
   python scripts/github_client.py blockers
   
   If blockers exist: STOP and report

2. Deploy to Yandex Cloud:
   ./scripts/deploy.sh serverless $TASK_ID

3. Health check:
   curl -f $DEPLOY_URL/health

4. Create Pull Request:
   gh pr create --title "feat: $TASK_ID" --body "[summary]"

5. Update YouTrack:
   python scripts/youtrack.py issue state $TASK_ID "Done"
   python scripts/youtrack.py issue comment $TASK_ID "[deployment info]"

6. Update KB release notes:
   python scripts/youtrack.py kb write "Retrospective/releases.md" "[notes]"
```

## Final Report

```
═══════════════════════════════════════════════════════════════
✅ PIPELINE COMPLETE: $TASK_ID
═══════════════════════════════════════════════════════════════

📋 BUSINESS (ultrathink)
   • BDD Scenarios: [X] features, [Y] scenarios
   • KB Updated: Context/current-sprint.md

🏗️ ARCHITECT (plan mode)
   • Stack: [tech stack]
   • ADRs: [count] decisions
   • Patterns: [list]

💻 DEVELOPER (TDD)
   • Cycles: [count]
   • Commits: [count]
   • Issues Fixed: [count]

🔍 QA (parallel subagents)
   • @test-analyzer: [X]% coverage, [Y] issues
   • @security-scanner: [Z] vulnerabilities
   • @code-reviewer: [W] suggestions

🚀 DEPLOYER
   • URL: [deploy_url]
   • PR: [pr_url]
   • YouTrack: Done

═══════════════════════════════════════════════════════════════
```

## Error Recovery

| Error | Action |
|-------|--------|
| YouTrack unavailable | Use cached KB, sync later |
| Tests failing | Create issues, continue with warning |
| Security CRITICAL | STOP pipeline, require manual fix |
| Deploy failure | Rollback, create incident |

Task ID or description: $ARGUMENTS
