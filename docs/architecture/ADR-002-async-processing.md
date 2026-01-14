# ADR-002: Async Processing with Background Tasks

**Status**: Accepted
**Date**: 2026-01-14
**Decision Makers**: ARCHITECT agent (via /run pipeline)
**Context**: POD-1 - Pipeline stages can be long-running

## Context and Problem Statement

The podcast generation pipeline has multiple stages that take time:
- News parsing: ~5-10 seconds
- LLM script generation: ~30-60 seconds
- TTS generation: ~60-120 seconds
- Upload to S3: ~10-20 seconds

Total: 2-4 minutes per episode.

How should we handle this async processing?

## Decision Drivers

- **User Experience**: Cron job doesn't need immediate response
- **Reliability**: Must handle failures at each stage
- **Observability**: Need to track progress
- **Cost**: Minimize resource usage

## Considered Options

### Option 1: Synchronous Sequential Processing
```python
def generate_episode():
    news = collect_news()  # blocking
    script = generate_script(news)  # blocking
    audio = generate_audio(script)  # blocking
    upload_audio(audio)  # blocking
```

**Pros**: Simple, easy to debug
**Cons**: No parallelization, long total time

### Option 2: Celery/Redis Task Queue
**Pros**: Industry standard, reliable, supports retries
**Cons**: Additional infrastructure (Redis), operational complexity, cost

### Option 3: FastAPI Background Tasks (CHOSEN)
```python
@app.post("/trigger")
async def trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(generate_episode_pipeline)
    return {"status": "started"}
```

**Pros**: Built into FastAPI, no external dependencies, simple
**Cons**: In-process (loses task if container restarts)

### Option 4: Yandex Cloud Functions chaining
**Pros**: Fully managed, auto-scaling
**Cons**: Complex orchestration, cold starts, expensive for our use case

## Decision Outcome

**Chosen option: FastAPI Background Tasks + State Persistence**

**Implementation**:
1. Use FastAPI BackgroundTasks for async execution
2. Persist state to YDB after each stage
3. If container restarts, resume from last completed stage

```python
async def episode_pipeline(episode_id: str):
    state = get_state(episode_id)

    if state.news_collected is False:
        news = await collect_news()
        save_state(episode_id, news_collected=True, news=news)

    if state.script_generated is False:
        script = await generate_script(state.news)
        save_state(episode_id, script_generated=True, script=script)

    # ... and so on
```

**State Schema** (YDB table `episode_states`):
```sql
CREATE TABLE episode_states (
    episode_id String,
    date Date,
    status String,  -- pending|processing|completed|failed
    news_collected Bool,
    script_generated Bool,
    audio_generated Bool,
    uploaded Bool,
    error_message String,
    updated_at Timestamp,
    PRIMARY KEY (episode_id)
)
```

## Parallelization Opportunities

Some stages CAN run in parallel:
- News parsing: Could parse multiple sources concurrently
- Audio generation: If we split into segments (not needed for 5min podcast)

For our scope, sequential is fine since total time is acceptable (~3 min).

## Retry Strategy

- News collection: Retry 3 times with exponential backoff (1s, 2s, 4s)
- LLM generation: Retry 2 times, then fallback to template
- TTS generation: Retry 3 times, then queue for later retry
- S3 upload: Retry indefinitely with backoff (eventual consistency)

## Consequences

**Positive**:
- No additional infrastructure needed
- Simple mental model
- Easy to debug (single process logs)
- State persistence enables resume on failure

**Negative**:
- If container crashes mid-pipeline, need to restart
- Not suitable for high-throughput workloads (fine for daily cron)

**Mitigation**:
- Health checks monitor pipeline progress
- Alert if pipeline runs > 10 minutes
- State table enables manual inspection and retry

## Alternatives for Future

If we need more robustness later:
- Migrate to Celery + Redis
- Or use Yandex Cloud Message Queue
- Or use Yandex Cloud Functions with Step Functions

## Validation

Success criteria:
- ✅ Pipeline completes in < 5 minutes
- ✅ Failures at any stage don't lose progress
- ✅ Can resume from last successful stage
- ✅ No external task queue needed

## Related Decisions

- ADR-003: Error handling and circuit breakers
- ADR-005: Observability and logging
