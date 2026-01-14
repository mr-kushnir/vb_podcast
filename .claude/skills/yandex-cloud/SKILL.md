---
description: "Yandex Cloud infrastructure. ACTIVATE for: deployment, YDB database, Object Storage S3, serverless containers, cloud setup, infrastructure"
allowed-tools: Bash, Read, Write
---

# Yandex Cloud Infrastructure Skill

## When This Skill Activates
- Setting up cloud infrastructure
- Working with YDB database
- Using Object Storage (S3)
- Deploying serverless containers
- Configuring service accounts

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                    YANDEX CLOUD                              │
│                                                              │
│  ┌──────────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │    Serverless    │  │     YDB     │  │    Object     │  │
│  │   Containers     │  │  Serverless │  │    Storage    │  │
│  └────────┬─────────┘  └──────┬──────┘  └───────┬───────┘  │
│           │                   │                 │           │
│           └───────────────────┼─────────────────┘           │
│                               │                              │
│                    ┌──────────┴──────────┐                  │
│                    │   Service Account   │                  │
│                    │    (IAM roles)      │                  │
│                    └─────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## YDB Quick Reference

### Create Table (YQL)
```sql
CREATE TABLE users (
    id Utf8,
    email Utf8,
    data Json,
    created_at Timestamp,
    PRIMARY KEY (id)
);

CREATE TABLE items (
    id Utf8,
    user_id Utf8,
    name Utf8,
    PRIMARY KEY (id),
    INDEX user_idx GLOBAL ON (user_id)
);
```

### Python Usage
```python
from src.db.ydb_client import get_db

db = get_db()

# Insert
db.insert('users', {
    'id': 'user-123',
    'email': 'test@example.com',
    'data': {'name': 'Test'}
})

# Select
users = db.select('users', where={'email': 'test@example.com'})

# Raw query
results = db.execute('SELECT * FROM users LIMIT 10')
```

## Object Storage Quick Reference

### Python Usage
```python
from src.storage.s3_client import get_storage

storage = get_storage()

# Upload
url = storage.upload_file('photo.jpg', 'photos/photo-123.jpg')
url = storage.upload_bytes(data, 'files/doc.pdf', 'application/pdf')

# Download
storage.download_file('photos/photo-123.jpg', '/tmp/photo.jpg')
data = storage.download_bytes('files/doc.pdf')

# Presigned URL (temporary access)
url = storage.get_presigned_url('private/file.pdf', expiration=3600)

# List
files = storage.list_objects(prefix='photos/')

# Delete
storage.delete('photos/old.jpg')
```

## Serverless Container

### Dockerfile Template
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### FastAPI Template with YDB + S3
```python
# src/main.py
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from src.db.ydb_client import get_db
from src.storage.s3_client import get_storage
import uuid

app = FastAPI()
db = get_db()
storage = get_storage()

class Item(BaseModel):
    name: str
    data: dict = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/items")
def create_item(item: Item):
    item_id = str(uuid.uuid4())
    db.insert('items', {
        'id': item_id,
        'name': item.name,
        'data': item.data
    })
    return {"id": item_id}

@app.get("/items/{item_id}")
def get_item(item_id: str):
    items = db.select('items', where={'id': item_id})
    if not items:
        raise HTTPException(404, "Not found")
    return items[0]

@app.post("/upload")
async def upload_file(file: UploadFile):
    object_name = f"uploads/{uuid.uuid4()}/{file.filename}"
    url = storage.upload_bytes(
        await file.read(),
        object_name,
        file.content_type
    )
    return {"url": url}
```

## Deploy Commands

```bash
# Full deploy (YDB + S3 + Container)
./scripts/deploy.sh deploy TASK-123

# Individual components
./scripts/deploy.sh ydb       # Setup YDB
./scripts/deploy.sh storage   # Setup Object Storage
./scripts/deploy.sh container # Deploy container only

# Operations
./scripts/deploy.sh status    # Check status
./scripts/deploy.sh health    # Health check
./scripts/deploy.sh rollback  # Rollback
```

## Environment Variables

```bash
# Required for YDB
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/xxx/xxx

# Required for S3
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
S3_BUCKET=bucket-name

# Required for deploy
YC_TOKEN=y0_xxx
YC_FOLDER_ID=xxx
YC_REGISTRY_ID=xxx
```

## Cost Optimization

| Resource | Free Tier | Notes |
|----------|-----------|-------|
| YDB Serverless | 1GB storage, 1M requests/month | Perfect for exam |
| Object Storage | 10GB, 10k requests | Plenty for files |
| Containers | Pay per invocation | Scales to zero |

## Common Issues

### YDB Connection
```python
# If auth fails, try metadata credentials (inside YC)
import ydb
creds = ydb.iam.MetadataUrlCredentials()
```

### S3 Signature Error
```python
# Ensure signature_version='s3v4' in boto config
from botocore.config import Config
config = Config(signature_version='s3v4')
```

### Container Won't Start
```bash
# Check logs
yc serverless container logs --name exam-container --limit 50
```
