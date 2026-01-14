#!/usr/bin/env python3
"""Create tasks in YouTrack for all issues"""

import sys
sys.path.insert(0, '.')
from scripts.youtrack import YouTrackClient

yt = YouTrackClient()

tasks = [
    {
        'summary': 'Implement ElevenLabs TTS integration',
        'description': '''# ElevenLabs Text-to-Speech Integration

## Problem
src/audio/tts.py raises NotImplementedError - audio generation blocked.

## Requirements
- Integrate ElevenLabs API
- Synthesize Russian text to MP3
- Circuit breaker for errors
- Upload to S3
- Unit tests

## Links
- GitHub: https://github.com/mr-kushnir/vb_podcast/issues/3'''
    },
    {
        'summary': 'Implement LLM script generation (YaGPT/Claude)',
        'description': '''# LLM Script Generation

## Problem
Only template fallback, no AI-generated scripts.

## Requirements
- YaGPT API (primary)
- Claude API (fallback)
- Engaging scripts (3-5 min)
- Humor and commentary
- Unit tests

## Links
- GitHub: https://github.com/mr-kushnir/vb_podcast/issues/3'''
    },
    {
        'summary': 'Increase test coverage from 14% to 70%+',
        'description': '''# Test Coverage Improvement

## Current: 14% (63/460 lines)
## Target: 70%+

## Priority modules:
- automation/pipeline.py (15+ tests)
- db/ydb_client.py (40+ tests)
- storage/s3_client.py (30+ tests)
- news/service.py (15+ tests)

## Links
- GitHub: https://github.com/mr-kushnir/vb_podcast/issues/1'''
    },
    {
        'summary': 'Deploy to Yandex Cloud Serverless Container',
        'description': '''# Production Deployment

## Prerequisites (must complete first):
- POD-2: Security fixes
- POD-3: TTS integration
- POD-4: LLM integration
- POD-5: Test coverage 70%+

## Steps:
- Build Docker image
- Deploy to YC
- Configure YDB/S3
- Set up cron (7:00 UTC)
- Health check'''
    }
]

for task_data in tasks:
    task = yt._request('POST', '/issues?fields=id,idReadable,summary', {
        'project': {'id': '0-2'},
        'summary': task_data['summary'],
        'description': task_data['description']
    })
    print(f"✅ Created {task.get('idReadable')}: {task.get('summary')}")

print('\n✅ All tasks created!')
print('View: https://mediapp.youtrack.cloud/projects/POD/issues')
