⚡ SPEED MODE: Maximum velocity, minimal documentation.

## Target: MVP in 15 minutes

### Shortcuts Applied
- Skip extensive KB documentation
- Minimal ADRs (just tech stack)
- Parallel everything possible
- Auto-commit enabled

## Compressed Pipeline

### Step 1: Quick Analysis (2 min)
```
Read task, create mental model.
Write 2-3 BDD scenarios (happy path + error).
NO extensive documentation.
```

### Step 2: Rapid Design (2 min)
```
Pick simplest tech stack.
Create basic structure.
Skip ADRs - document in code comments.
```

### Step 3: TDD Sprint (8 min)
```
For each scenario:
1. Test → commit
2. Code → commit  
3. Next

Target: 3 commits per scenario
Push every 5 minutes
```

### Step 4: Quick QA (2 min)
```
Run in parallel (don't wait):
- pytest tests/ -x
- bandit -r src/ -ll -q

Create issues only for CRITICAL findings.
```

### Step 5: Deploy (1 min)
```
./scripts/deploy.sh serverless
git push
Close YouTrack task
```

## Skip in Speed Mode
- ❌ Detailed KB articles
- ❌ Multiple ADRs
- ❌ Comprehensive security scan
- ❌ Code review subagent
- ❌ Extensive test coverage

## Keep in Speed Mode
- ✅ BDD feature file (minimal)
- ✅ Working tests (basic)
- ✅ Commits (frequent, short messages)
- ✅ Deploy + health check
- ✅ YouTrack status update

## Output

```
⚡ QUICK PIPELINE COMPLETE

Task: $TASK_ID → Done
Time: [X] minutes
Tests: [Y] passing
Deploy: [URL]
Commits: [Z]
```

Task: $ARGUMENTS
