# 🤖 MULTI-AGENT EXAM SYSTEM v3.0 (Jan 2026)

## Latest Claude Code Features Applied

This system leverages cutting-edge capabilities:
- **Ultrathink Mode**: Maximum reasoning for complex tasks
- **Custom Subagents**: Specialized AI workers with isolated contexts  
- **Skills**: Auto-discovered capabilities with progressive disclosure
- **Hooks**: Automated quality gates and workflow triggers
- **LSP Integration**: Go-to-definition, find references
- **Async Agents**: Parallel execution without blocking
- **Plan Mode + Revving**: Iterative improvement cycles

---

## 🧠 Ultrathink Methodology

### Thinking Budget Keywords
```
think         → Basic extended thinking (~8k tokens)
think hard    → Deeper analysis (~16k tokens)
think harder  → Complex problems (~24k tokens)  
ultrathink    → Maximum reasoning (~32k+ tokens)
```

**IMPORTANT**: Only `ultrathink` works in v2.0+. Previous keywords disabled.

### Ultrathink Best Practices
1. Use for architectural decisions, not simple tasks
2. Combine with Plan Mode for complex features
3. Apply "revving" - critique and iterate plans
4. Don't spam - expensive in tokens

### Revving Pattern (Iterative Improvement)
```
Step 1: "ultrathink and create a plan for [task]"
Step 2: "Critique this plan - what edge cases are missing?"
Step 3: "Revise plan based on critique"  
Step 4: "One more critique round focusing on [aspect]"
Step 5: "Execute the final plan"
```

---

## 🤖 Subagent Architecture

### Built-in Subagents
| Agent | Purpose | Model | Tools |
|-------|---------|-------|-------|
| Explore | File search, codebase analysis | Haiku | Glob, Grep, Read |
| Task | General execution | Sonnet | All |

### Custom Subagents Structure
```yaml
# .claude/agents/code-reviewer.md
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
model: sonnet
tools: Read, Glob, Grep
---

You are a code reviewer. Analyze code and provide actionable feedback on:
- Code quality and readability
- Security vulnerabilities
- Performance issues
- Best practice violations

Focus on HIGH and CRITICAL issues. Skip minor style issues.
```

### Subagent Delegation in CLAUDE.md
```markdown
## 👥 SUB-AGENT DELEGATION SYSTEM

**BE PROACTIVE WITH SUB-AGENTS!**

ALWAYS delegate to specialists:
- Exploration tasks → @explore-agent
- Code review → @code-reviewer  
- Security scan → @security-scanner
- Test analysis → @test-analyzer

Launch PARALLEL subagents when tasks are independent.
```

### Async Subagent Workflow
```
1. Launch subagent with Ctrl+B (backgrounds it)
2. Continue working on other tasks
3. Get notification when subagent completes
4. Review results and integrate
```

### Resume Subagents
```
"Resume the code-reviewer subagent and continue where it stopped"
```
Preserves full history including tool calls.

---

## 📚 Skills System (Oct 2025+)

### How Skills Work
1. Claude scans skill descriptions at task start
2. Matches relevant skills to conversation context
3. Progressively loads instructions (saves tokens)
4. Applies patterns automatically

### Skill Structure
```
.claude/skills/
├── bdd-testing/
│   ├── SKILL.md           # Main instructions (required)
│   ├── templates/         # Gherkin templates
│   │   └── feature.template
│   └── examples/          # Working examples
│       └── registration.feature
├── tdd-workflow/
│   └── SKILL.md
├── security-scan/
│   └── SKILL.md
└── youtrack-integration/
    └── SKILL.md
```

### SKILL.md Format
```markdown
---
description: "BDD testing with Gherkin scenarios. ACTIVATE when: writing tests, creating features, TDD workflow"
allowed-tools: Task, Read, Write, Bash
---

# BDD Testing Skill

## When to Use
- Creating new features
- Writing acceptance criteria
- Test-first development

## Templates
Load templates from ./templates/ directory

## Workflow
1. Write Gherkin scenario
2. Generate step definitions
3. Implement code to pass
```

### Skills vs Subagents Decision Matrix
| Need | Use |
|------|-----|
| Patterns, templates, workflows | Skills |
| Heavy computation, exploration | Subagents |
| Auto-triggered by context | Skills |
| Explicit delegation | Subagents |
| Shared context needed | Skills |
| Isolated context needed | Subagents |

---

## 🔗 Hooks System

### Hook Events
```
PreToolUse      → Before tool executes (can block)
PostToolUse     → After tool completes
SessionStart    → Claude Code starts
Stop            → Claude finishes response
SubagentStop    → Subagent completes
PermissionRequest → On permission prompts
```

### settings.json Hooks Configuration
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/auto_lint.py"
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/commit_if_tests_pass.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/security_gate.py"
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/sync_youtrack_context.py"
          }
        ]
      }
    ]
  }
}
```

### Useful Hook Patterns

**Auto-test after file changes:**
```json
{"matcher": "Write", "command": "pytest tests/ -x --tb=short"}
```

**Security check before bash:**
```json
{"matcher": "Bash", "command": "bandit -r src/ -ll -q"}
```

**Sync KB on session start:**
```json
{"event": "SessionStart", "command": "python scripts/kb_sync.py"}
```

**Auto-commit on successful tests:**
```json
{"matcher": "Bash(*test*)", "command": "git add -A && git commit -m 'auto: tests passing'"}
```

---

## 🔄 Workflow Patterns

### Pattern 1: Explore → Plan → Execute
```
1. "ultrathink and launch Explore subagent to understand [feature area]"
   → Subagent searches, returns summary
   → Main context stays clean

2. "Based on exploration, create detailed implementation plan"
   → Plan mode with thinking
   → Document decisions

3. "Execute plan step by step with TDD"
   → Red-green-refactor cycle
   → Commit after each green
```

### Pattern 2: Parallel Subagents
```
"Launch these subagents IN PARALLEL:
1. @explore-agent: scan src/ for relevant files
2. @security-scanner: check for vulnerabilities
3. @test-analyzer: review test coverage gaps

Synthesize findings when all complete."
```

### Pattern 3: Split Role Analysis
```
"Analyze this design using split perspectives:
- Subagent 1 (Devil's Advocate): Find problems and risks
- Subagent 2 (Optimist): Find opportunities and benefits
- Subagent 3 (Pragmatist): Assess feasibility and timeline

Each uses ultrathink. Synthesize into balanced recommendation."
```

### Pattern 4: Git Worktree Parallelism
```bash
# Terminal 1: Feature A
git worktree add ../project-feature-a feature-a
cd ../project-feature-a && claude

# Terminal 2: Feature B  
git worktree add ../project-feature-b feature-b
cd ../project-feature-b && claude
```

---

## 📊 Context Management

### Monitor Usage
```
/context   → Visual context breakdown
/stats     → Session statistics
```

### Context Strategy
1. **Start subagents at 40%** → Keep main context clean
2. **Compact at 60%** → Before getting constrained
3. **Handoff at 80%** → Start fresh conversation

### Auto-Compact Buffer Trade-off
```
Default max_output_tokens → 32k buffer (22% of 200k)
64k max_output_tokens → ~40% buffer reserved

Higher output = less context for code. Balance accordingly.
```

### Reduce Context Bloat
- Remove unused MCP servers (each adds overhead)
- Use skills progressive disclosure
- Delegate exploration to subagents
- Don't paste entire files when @ reference works

---

## 🎯 Exam Optimization Strategies

### Speed Tactics
1. **Prepare skills** before exam: BDD templates, test patterns
2. **Prepare subagents**: Specialized reviewers ready to go
3. **Use ultrathink sparingly**: Only for hard decisions
4. **Parallel subagents**: Explore + Security + Tests simultaneously
5. **Hooks for automation**: Auto-lint, auto-test, auto-commit

### Token Efficiency
1. **Subagents for exploration**: Don't pollute main context
2. **Skills for patterns**: Reuse templates, don't regenerate
3. **@ file references**: Instead of pasting content
4. **Short prompts**: Be concise, Claude understands

### Quality Assurance Pipeline
```
PostToolUse(Write) → Lint check
PostToolUse(Write) → Run relevant tests
PostToolUse(Bash) → Security scan
Stop → Update YouTrack status
SubagentStop → Integrate findings
```

### Commit Strategy
```
test(scope): red: failing test for [scenario]
feat(scope): green: implement [feature]
refactor(scope): improve [component]
fix(scope): resolve #issue
security(scope): fix vulnerability
```

---

## 🔧 Environment Setup

### Required in .env
```bash
YOUTRACK_URL=https://xxx.youtrack.cloud
YOUTRACK_TOKEN=perm:xxx
YOUTRACK_PROJECT=EXAM
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=user/repo
YC_TOKEN=y0_xxx
YC_FOLDER_ID=xxx
```

### Claude Code Settings
```bash
# Enable LSP
/lsp

# Custom status line
/statusline

# View context
/context

# Background tasks
Ctrl+B  # Send to background
/tasks  # View tasks
```

### Model Selection
- **Opus 4.5**: Complex tasks, architecture, ultrathink
- **Sonnet 4.5**: Daily development, fast iteration
- **Haiku 4.5**: Exploration subagents, quick checks

---

## 📝 Quick Reference

### Slash Commands
```
/plan         → Enter plan mode
/context      → Show context usage
/tasks        → Background tasks
/agents       → Manage subagents
/compact      → Compress conversation
/lsp          → Language Server Protocol
```

### Keyboard Shortcuts
```
Shift+Tab     → Toggle auto-accept edits
Ctrl+B        → Background current task
Alt+Tab       → Toggle thinking display
Tab           → Accept suggestion
```

### Subagent Invocation
```
@explore-agent analyze the authentication module
@code-reviewer check src/handlers/
@security-scanner scan for vulnerabilities
```
