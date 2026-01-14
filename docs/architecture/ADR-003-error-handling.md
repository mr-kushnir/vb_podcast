# ADR-003: Graceful Degradation and Error Handling

**Status**: Accepted
**Date**: 2026-01-14
**Decision Makers**: ARCHITECT agent (via /run pipeline)
**Context**: POD-1 - Pipeline depends on external APIs that can fail

## Context and Problem Statement

The pipeline depends on multiple external services:
- TechCrunch (web scraping)
- YaGPT/Claude API (LLM)
- ElevenLabs (TTS)
- Yandex S3 (storage)

Any of these can fail. How do we ensure the system remains functional?

## Decision Drivers

- **Availability**: Publish an episode every day, even if APIs are down
- **User Experience**: Show something useful even if not perfect
- **Cost**: Don't waste API quota on failing requests
- **Debugging**: Need visibility into what failed and why

## Core Principles

### 1. Graceful Degradation Hierarchy

```
IDEAL:    Fresh news → LLM script → High-quality TTS → Published episode
                ↓              ↓              ↓              ↓
FALLBACK: Cached news → Template script → Local TTS → Text-only episode
```

### 2. Circuit Breaker Pattern

Don't repeatedly call failing services:

```python
class CircuitBreaker:
    states = {CLOSED, OPEN, HALF_OPEN}
    failure_threshold = 3
    timeout = 300  # 5 minutes

    def call(self, func):
        if self.state == OPEN:
            if time.now() < self.open_until:
                raise CircuitBreakerOpen("Service unavailable")
            else:
                self.state = HALF_OPEN

        try:
            result = func()
            self.reset_failures()
            return result
        except Exception as e:
            self.record_failure()
            if self.failures >= self.failure_threshold:
                self.state = OPEN
                self.open_until = time.now() + self.timeout
            raise
```

### 3. Retry with Exponential Backoff

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.RequestException)
)
async def fetch_news():
    response = await client.get(url)
    return response.json()
```

## Decision Matrix: What to Do When Things Fail

### News Collection Fails

| Scenario | Action | Rationale |
|----------|--------|-----------|
| TechCrunch down | Use cached news from yesterday | Better stale news than no episode |
| HTML structure changed | Alert + use cache | Need manual fix, but don't block |
| Rate limited | Wait + retry | Respect rate limits |
| No articles in 24h | Use last 48h | Better broader time window than no content |

### LLM Script Generation Fails

| Scenario | Action | Rationale |
|----------|--------|-----------|
| API down | Template-based script | Formulaic but functional |
| Timeout | Retry with shorter prompt | Maybe it was too complex |
| Quota exceeded | Use template + alert | Upgrade plan or wait for reset |
| Inappropriate output | Regenerate with stricter prompt | Safety first |

### TTS Generation Fails

| Scenario | Action | Rationale |
|----------|--------|-----------|
| API down | Publish script text only | Users can read instead |
| Quota exceeded | Queue for retry in 1 hour | Will likely reset soon |
| Poor quality | Accept but flag | Some audio > no audio |
| Timeout | Retry with lower quality | Faster generation |

### Storage Upload Fails

| Scenario | Action | Rationale |
|----------|--------|-----------|
| S3 down | Keep local + retry later | Critical to not lose audio |
| Network error | Retry indefinitely | Eventually will succeed |
| Quota full | Alert + stop | Need manual intervention |

## Fallback Content Strategy

### Template Script Example

```python
TEMPLATE = """
Доброе утро! С вами AI Morning Podcast.

Сегодня, {date}, у нас {article_count} интересных новостей из мира AI:

{news_summaries}

Это был краткий обзор AI новостей. Следите за обновлениями!
"""
```

### Cached News

- Store last 7 days of news in YDB
- If fresh fetch fails, use most recent cache
- Always prefer fresher data

### Local TTS Fallback

If ElevenLabs fails completely:
- Option A: Use Yandex SpeechKit (Russian cloud TTS)
- Option B: Use gTTS (Google TTS, free but lower quality)
- Option C: Text-only episode

## Alerting Strategy

**CRITICAL**: Episode completely failed to generate
→ Send Telegram alert immediately

**WARNING**: Used fallback (cached news, template script, etc.)
→ Log + send daily summary

**INFO**: Retry succeeded after initial failure
→ Log only

## Consequences

**Positive**:
- High availability even with flaky dependencies
- Users always get something useful
- Cost-effective (don't waste quota on repeated failures)

**Negative**:
- More complex logic
- Need to maintain fallback content
- Harder to test all failure scenarios

**Mitigation**:
- Comprehensive BDD scenarios for each failure mode
- Regular testing of fallback paths
- Monitor fallback usage (high usage = investigate)

## Validation

Success criteria:
- ✅ 99% episode publication rate (even with API failures)
- ✅ No cascading failures
- ✅ Circuit breakers prevent quota waste
- ✅ Alerts sent for actionable failures only

## Implementation Checklist

- [ ] Implement CircuitBreaker class
- [ ] Add retry decorators to all external calls
- [ ] Create template script generator
- [ ] Set up news caching in YDB
- [ ] Implement fallback TTS options
- [ ] Configure Telegram alerts
- [ ] Add metrics for fallback usage

## Related Decisions

- ADR-002: Async processing
- ADR-004: Data storage and caching
- ADR-005: Observability
