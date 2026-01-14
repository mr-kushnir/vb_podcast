#!/usr/bin/env python3
"""Create Knowledge Base articles in YouTrack"""

import sys
sys.path.insert(0, '.')
from scripts.youtrack import YouTrackClient

yt = YouTrackClient()

# Article 2: Architecture Decisions
arch_content = """# Architecture Decision Records - POD-1

## ADR-001: Modular Monolith Architecture
**Decision**: Use modular monolith (FastAPI) over microservices
**Rationale**: Simplicity, low cost, appropriate for daily cron + low-traffic portal

## ADR-002: Async Processing with Background Tasks
**Decision**: FastAPI BackgroundTasks + YDB state persistence
**Rationale**: No external task queue needed, state enables resume on failure

## ADR-003: Graceful Degradation and Error Handling
**Decision**: Circuit breakers, retry with backoff, fallback strategies
**Rationale**: High availability even with API failures

## ADR-004: Data Storage Strategy
**Decision**: Yandex YDB (metadata) + S3 (audio files)
**Rationale**: Serverless, auto-scaling, cost-effective (~$3/month)

---
Full ADRs: https://github.com/mr-kushnir/vb_podcast/tree/main/docs/architecture
"""

arch_article = yt._request('POST', '/articles?fields=id,idReadable,summary', {
    'project': {'id': '0-2'},
    'summary': 'Architecture: Decision Records',
    'content': arch_content
})

print('✅ Architecture article:', arch_article.get('idReadable'), '-', arch_article.get('summary'))

# Article 3: QA Report
qa_content = """# QA Analysis Report - POD-1

**Date**: 2026-01-14
**Analysis**: 3 parallel subagents

## CRITICAL: Test Coverage 14%
- Overall: 14% (63/460 lines)
- Untested: pipeline, db, storage (0% each)
- Target: 70%+ coverage
- GitHub Issue #1: https://github.com/mr-kushnir/vb_podcast/issues/1

## HIGH: Security Vulnerabilities
1. SQL Injection (CWE-89) in ydb_client.py
2. Weak MD5 hash (CWE-327) in parser.py
3. Unsafe network binding in main.py
- GitHub Issue #2: https://github.com/mr-kushnir/vb_podcast/issues/2

## BLOCKER: Unimplemented Features
1. TTS Service (ElevenLabs) - NotImplementedError
2. LLM Script Generation - template fallback only
3. Missing Dependency Injection pattern
- GitHub Issue #3: https://github.com/mr-kushnir/vb_podcast/issues/3

## Deployment Status
**BLOCKED** by:
- Test coverage < 70%
- SQL injection vulnerabilities
- Core features unimplemented

Estimated time to production: 3-4 weeks
"""

qa_article = yt._request('POST', '/articles?fields=id,idReadable,summary', {
    'project': {'id': '0-2'},
    'summary': 'QA Report: Issues & Blockers',
    'content': qa_content
})

print('✅ QA article:', qa_article.get('idReadable'), '-', qa_article.get('summary'))

print('\n✅ Knowledge Base articles created successfully!')
print('View at: https://mediapp.youtrack.cloud/articles/POD')
