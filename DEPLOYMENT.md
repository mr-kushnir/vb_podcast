# Deployment Guide - Yandex Cloud

## Prerequisites

### 1. Install Required Tools

```bash
# Yandex Cloud CLI
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# jq (JSON processor)
# Ubuntu/Debian:
sudo apt-get install jq
# MacOS:
brew install jq
# Windows (WSL):
sudo apt-get install jq

# Docker (if not installed)
# Follow: https://docs.docker.com/engine/install/
```

### 2. Configure Yandex Cloud CLI

```bash
# Initialize with OAuth token from .env
yc init --token $YC_TOKEN

# Set folder
yc config set folder-id $YC_FOLDER_ID

# Configure Docker registry
yc container registry configure-docker
```

### 3. Verify Configuration

```bash
# Check .env file has all required variables
cat .env | grep -E "YC_TOKEN|YC_FOLDER_ID|YC_REGISTRY_ID"

# Test YC CLI
yc config list
```

## Deployment Steps

### Quick Deploy (Automated)

```bash
# Full deployment with auto-setup
chmod +x scripts/deploy.sh
./scripts/deploy.sh deploy pod vb-podcast

# This will:
# 1. Create YDB database
# 2. Set up S3 bucket
# 3. Build Docker image
# 4. Push to registry
# 5. Deploy serverless container
# 6. Run health check
```

### Manual Deploy (Step by Step)

#### 1. Set Up YDB Database

```bash
./scripts/deploy.sh ydb pod
```

This creates a serverless YDB database and runs migrations.

#### 2. Set Up Object Storage

```bash
./scripts/deploy.sh storage pod
```

This creates:
- S3-compatible bucket
- Service account with permissions
- Access keys

#### 3. Build Container

```bash
./scripts/deploy.sh build pod
```

Builds Docker image from Dockerfile.

#### 4. Push to Registry

```bash
./scripts/deploy.sh push pod
```

Pushes image to Yandex Container Registry.

#### 5. Deploy Container

```bash
./scripts/deploy.sh container pod
```

Deploys serverless container with environment variables.

#### 6. Health Check

```bash
./scripts/deploy.sh health pod
```

Verifies container is healthy.

## Environment Variables

The following variables are injected into the container:

```bash
# Yandex Cloud
YC_TOKEN              # OAuth token
YC_FOLDER_ID          # Folder ID
YC_SERVICE_ACCOUNT_ID # Service account

# Database
YDB_ENDPOINT          # YDB connection endpoint
YDB_DATABASE          # Database path

# Storage
S3_BUCKET             # Bucket name
AWS_ACCESS_KEY_ID     # S3 access key
AWS_SECRET_ACCESS_KEY # S3 secret key

# APIs
ELEVENLABS_API_KEY    # TTS service
YAGPT_API_KEY         # Optional: YaGPT
CLAUDE_API_KEY        # Optional: Claude

# Application
DEBUG=false           # Production mode
PORT=8080            # Container port
```

## Post-Deployment

### 1. Get Container URL

```bash
yc serverless container get exam-podvbpodcast --format json | jq -r '.url'
```

### 2. Test Endpoints

```bash
# Health check
curl https://your-container-url.apigw.yandexcloud.net/health

# API info
curl https://your-container-url.apigw.yandexcloud.net/

# List episodes
curl https://your-container-url.apigw.yandexcloud.net/api/episodes
```

### 3. Check Status

```bash
./scripts/deploy.sh status pod
```

### 4. View Logs

```bash
yc logging read --group-id=$(yc serverless container get exam-podvbpodcast --format json | jq -r '.log_group_id') --since 1h
```

## Automation

### Set Up Cron Trigger (7:00 UTC Daily)

```bash
# Create trigger for daily episode generation
yc serverless trigger create timer \
    --name daily-podcast-generator \
    --cron-expression "0 7 * * ? *" \
    --invoke-container-id $(yc serverless container get exam-podvbpodcast --format json | jq -r '.id') \
    --invoke-container-path /api/automation/generate \
    --invoke-container-service-account-id $YC_SERVICE_ACCOUNT_ID
```

## Monitoring

### Container Metrics

```bash
# CPU and memory usage
yc monitoring metric-data read \
    --metric-name container.cpu_usage \
    --container-id $(yc serverless container get exam-podvbpodcast --format json | jq -r '.id')
```

### Application Logs

```bash
# Real-time logs
yc logging read --follow --group-id=$(yc serverless container get exam-podvbpodcast --format json | jq -r '.log_group_id')

# Error logs
yc logging read --filter 'level=ERROR' --group-id=$(yc serverless container get exam-podvbpodcast --format json | jq -r '.log_group_id')
```

## Rollback

If deployment fails or issues are detected:

```bash
# Automatic rollback to previous revision
./scripts/deploy.sh rollback pod
```

## Costs Estimate

- **Serverless Container**: ~$3-5/month (100 req/day)
- **YDB Serverless**: ~$1-2/month (minimal usage)
- **S3 Storage**: ~$0.50/month (1GB audio files)
- **Total**: ~$5-7/month

## Troubleshooting

### Container Not Starting

```bash
# Check container logs
yc logging read --group-id=$(yc serverless container get exam-podvbpodcast --format json | jq -r '.log_group_id') --since 1h

# Check container revision
yc serverless container revision get $(yc serverless container get exam-podvbpodcast --format json | jq -r '.revision_id')
```

### Database Connection Issues

```bash
# Test YDB connection
yc ydb database get exam-podvbpodcast-db

# Run query
yc ydb scripting yql --database /ru-central1/.../exam-podvbpodcast-db --script "SELECT 1;"
```

### S3 Upload Failures

```bash
# Check bucket permissions
yc storage bucket get exam-podvbpodcast-files

# Test S3 access
aws s3 ls s3://exam-podvbpodcast-files --endpoint-url=https://storage.yandexcloud.net
```

## Security

### Secrets Management

Never commit secrets to Git. Use:

1. **Environment variables** in container
2. **Lockbox** for sensitive data (optional)
3. **Service accounts** with minimal permissions

### Update Credentials

```bash
# Rotate S3 keys
yc iam access-key create --service-account-name exam-podvbpodcast-sa

# Update container with new keys
yc serverless container revision deploy \
    --container-name exam-podvbpodcast \
    --image cr.yandex/... \
    --environment AWS_ACCESS_KEY_ID=new_key,AWS_SECRET_ACCESS_KEY=new_secret
```

## Support

For issues:
1. Check logs: `./scripts/deploy.sh status pod`
2. Review YC documentation: https://cloud.yandex.com/docs
3. GitHub Issues: https://github.com/mr-kushnir/vb_podcast/issues
