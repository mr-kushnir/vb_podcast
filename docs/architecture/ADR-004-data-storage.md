# ADR-004: Data Storage Strategy

**Status**: Accepted
**Date**: 2026-01-14
**Decision Makers**: ARCHITECT agent (via /run pipeline)
**Context**: POD-1 - Need to store episodes, metadata, cache

## Context and Problem Statement

What storage systems should we use for:
1. Episode metadata (date, duration, URLs, status)
2. News articles (raw data, cache)
3. Generated scripts (text)
4. Audio files (MP3)
5. Application state (pipeline progress)

## Decision Drivers

- **Cost**: Minimize storage costs
- **Performance**: Fast reads for web portal
- **Simplicity**: Minimize infrastructure
- **Scalability**: Handle 365+ episodes/year
- **Integration**: Work well with Yandex Cloud

## Storage Decision Matrix

| Data Type | Storage | Rationale |
|-----------|---------|-----------|
| Episode metadata | **Yandex YDB (serverless)** | Structured data, ACID, auto-scaling, SQL-like queries |
| Audio files | **Yandex Object Storage (S3)** | Large files, CDN integration, cost-effective |
| Scripts (text) | **YDB or S3** | Small files, store in YDB for fast access |
| News cache | **YDB** | Structured, need filtering/querying |
| Pipeline state | **YDB** | Need transactional updates |
| Application config | **.env + YDB** | Environment vars for secrets, YDB for dynamic config |

## Database Schema (Yandex YDB)

### Table: episodes

```sql
CREATE TABLE episodes (
    episode_id String,
    date Date,
    status String,  -- pending|processing|completed|failed
    article_count Uint32,
    script_text String,
    script_word_count Uint32,
    audio_url String,
    audio_duration_seconds Uint32,
    audio_file_size_bytes Uint64,
    created_at Timestamp,
    published_at Timestamp,
    PRIMARY KEY (episode_id),
    INDEX idx_date (date)
)
```

### Table: news_articles

```sql
CREATE TABLE news_articles (
    article_id String,
    episode_id String,
    title String,
    description String,
    url String,
    published_at Timestamp,
    source String,  -- 'techcrunch'
    scraped_at Timestamp,
    PRIMARY KEY (article_id),
    INDEX idx_episode (episode_id),
    INDEX idx_published (published_at)
)
```

### Table: pipeline_states

```sql
CREATE TABLE pipeline_states (
    episode_id String,
    stage String,  -- news|script|audio|upload
    status String,  -- pending|running|completed|failed
    started_at Timestamp,
    completed_at Timestamp,
    error_message String,
    retry_count Uint32,
    PRIMARY KEY (episode_id, stage)
)
```

### Table: cache_metadata

```sql
CREATE TABLE cache_metadata (
    cache_key String,
    data_json String,  -- JSON serialized data
    expires_at Timestamp,
    created_at Timestamp,
    PRIMARY KEY (cache_key)
)
```

## Object Storage Structure (S3)

```
podcasts/
├── audio/
│   ├── 2026-01-14.mp3
│   ├── 2026-01-15.mp3
│   └── ...
├── scripts/
│   ├── 2026-01-14.txt
│   └── ...
└── archive/
    └── old-episodes/  # moved after 30 days
```

## Caching Strategy

### Level 1: In-Memory (Application)
- Recent episodes (last 7 days)
- TTL: 1 hour
- Size limit: 100MB
- Eviction: LRU

### Level 2: YDB Cache Table
- News articles (last 30 days)
- Generated scripts (last 90 days)
- TTL: Based on content type
- Cleanup: Daily cron job

### Level 3: S3 (Long-term)
- All audio files (indefinite, with lifecycle policy)
- Old scripts (>90 days, moved to cold storage)

## Data Lifecycle

### Episode Data

```
Day 0: Create episode
  ↓
Day 1-7: Hot data (in-memory + YDB + S3)
  ↓
Day 8-30: Warm data (YDB + S3)
  ↓
Day 31-365: Archive (YDB metadata only, S3 standard)
  ↓
Day 366+: Cold archive (YDB metadata, S3 glacier)
```

### Lifecycle Policies

**S3 Lifecycle**:
- audio/: Keep in standard storage for 30 days → Move to Glacier
- scripts/: Keep for 90 days → Delete (already in YDB)

**YDB Cleanup**:
- Delete news_articles older than 90 days (keep episode references)
- Keep episodes table indefinitely (metadata is small)

## Backup Strategy

**YDB**:
- Automatic backups by Yandex (serverless YDB includes this)
- Point-in-time recovery available

**S3**:
- Versioning enabled
- Cross-region replication (optional, if budget allows)
- Manual backup: Critical audio files to separate bucket monthly

## Performance Optimization

### Indexing

- `episodes`: Primary index on `episode_id`, secondary on `date`
- `news_articles`: Composite index on `(published_at, source)`
- `pipeline_states`: Composite index on `(episode_id, stage)`

### Query Patterns

**Most common queries**:
1. Get latest episode: `SELECT * FROM episodes ORDER BY date DESC LIMIT 1`
2. Get episode by date: `SELECT * FROM episodes WHERE date = ?`
3. List recent episodes: `SELECT * FROM episodes ORDER BY date DESC LIMIT 10`
4. Check pipeline status: `SELECT * FROM pipeline_states WHERE episode_id = ?`

All optimized with indexes.

## Cost Estimation

**YDB** (serverless):
- Storage: ~1 GB/year = $0.02/month
- Requests: ~1000/day = negligible
- **Total**: ~$0.50/month

**S3**:
- Storage: ~150 MB/episode × 365 = ~55 GB/year
- At $0.02/GB = ~$1.10/month
- Egress: ~10 GB/month (users) = ~$1.00/month
- **Total**: ~$2.10/month

**Grand Total**: ~$2.60/month for storage (very affordable)

## Migration Path

If we outgrow this:
1. YDB scales automatically (serverless)
2. S3 scales automatically
3. If needed, add CloudFront CDN ($5-10/month)
4. If needed, Redis cache layer ($10-20/month)

But current design should handle 1000+ episodes and 100K+ visits/month.

## Consequences

**Positive**:
- Low cost
- Auto-scaling (serverless YDB)
- Integrated with Yandex Cloud
- Simple to operate

**Negative**:
- Vendor lock-in to Yandex Cloud
- YDB is less mature than PostgreSQL
- Need to learn YQL (YDB query language)

**Mitigation**:
- Keep SQL-like queries (easy to migrate)
- Use abstraction layer (Repository pattern)
- Export backups regularly

## Validation

Success criteria:
- ✅ All queries return in < 100ms
- ✅ Storage cost < $5/month
- ✅ No data loss
- ✅ Easy to query for debugging

## Implementation Tasks

- [ ] Create YDB tables with migrations
- [ ] Set up S3 bucket with lifecycle policies
- [ ] Implement Repository pattern for data access
- [ ] Add caching layer
- [ ] Configure automated backups
- [ ] Create cleanup cron jobs

## Related Decisions

- ADR-001: Modular monolith (single database)
- ADR-003: Error handling (state persistence)
- ADR-006: API integration (data flow)
