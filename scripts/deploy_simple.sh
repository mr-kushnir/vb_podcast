#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Simple Deploy Script for Yandex Cloud (no jq required)
# ═══════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Arguments
COMMAND="${1:-deploy}"
TASK_ID="${2:-pod}"
VERSION="${3:-$(date +%Y%m%d-%H%M%S)}"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# Container name
CONTAINER_NAME="exam-$(echo $TASK_ID | tr '[:upper:]' '[:lower:]' | tr -d '-')vbpodcast"
IMAGE_NAME="cr.yandex/$YC_REGISTRY_ID/$CONTAINER_NAME:$VERSION"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Deploying: $CONTAINER_NAME${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

# ═══════════════════════════════════════════════════════════
# Step 1: Configure YC
# ═══════════════════════════════════════════════════════════
echo -e "${BLUE}🔧 Configuring Yandex Cloud...${NC}"
yc config set token $YC_TOKEN 2>/dev/null || true
yc config set folder-id $YC_FOLDER_ID 2>/dev/null || true
yc container registry configure-docker 2>/dev/null || true
echo -e "${GREEN}✅ Configured${NC}"

# ═══════════════════════════════════════════════════════════
# Step 2: Setup YDB Database
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}📊 Setting up YDB...${NC}"

DB_NAME="$CONTAINER_NAME-db"

# Check if database exists (simple check)
if yc ydb database get "$DB_NAME" &>/dev/null; then
    echo "Database already exists"
else
    echo "Creating YDB database..."
    yc ydb database create \
        --name "$DB_NAME" \
        --serverless \
        --folder-id $YC_FOLDER_ID

    echo "Waiting for database..."
    sleep 15
fi

# Get database info (without jq)
export YDB_ENDPOINT=$(yc ydb database get "$DB_NAME" --format json-rest | grep -o '"endpoint":"[^"]*"' | cut -d'"' -f4)
export YDB_DATABASE=$(yc ydb database get "$DB_NAME" --format json-rest | grep -o '"database_path":"[^"]*"' | cut -d'"' -f4)

echo -e "${GREEN}✅ YDB ready${NC}"

# Run migrations if exists
if [ -f "migrations/tables.yql" ]; then
    echo "Running migrations..."
    yc ydb scripting yql \
        --database $YDB_DATABASE \
        --script-file migrations/tables.yql 2>/dev/null || echo "Migrations already applied"
fi

# ═══════════════════════════════════════════════════════════
# Step 3: Setup Object Storage
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}📦 Setting up Object Storage...${NC}"

BUCKET_NAME="$CONTAINER_NAME-files"
SA_NAME="$CONTAINER_NAME-sa"

# Check if service account exists
if yc iam service-account get "$SA_NAME" &>/dev/null; then
    echo "Service account exists"
    export YC_SERVICE_ACCOUNT_ID=$(yc iam service-account get "$SA_NAME" --format json-rest | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
else
    echo "Creating service account..."
    yc iam service-account create --name "$SA_NAME"

    export YC_SERVICE_ACCOUNT_ID=$(yc iam service-account get "$SA_NAME" --format json-rest | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    echo "Granting permissions..."
    yc resource-manager folder add-access-binding $YC_FOLDER_ID \
        --role storage.editor \
        --subject serviceAccount:$YC_SERVICE_ACCOUNT_ID 2>/dev/null || true
    yc resource-manager folder add-access-binding $YC_FOLDER_ID \
        --role ydb.editor \
        --subject serviceAccount:$YC_SERVICE_ACCOUNT_ID 2>/dev/null || true
    yc resource-manager folder add-access-binding $YC_FOLDER_ID \
        --role serverless.containers.invoker \
        --subject serviceAccount:$YC_SERVICE_ACCOUNT_ID 2>/dev/null || true
fi

# Check if bucket exists (simple way)
if yc storage bucket get $BUCKET_NAME &>/dev/null; then
    echo "Bucket already exists"
else
    echo "Creating bucket..."
    yc storage bucket create \
        --name $BUCKET_NAME \
        --default-storage-class standard \
        --max-size 1073741824 2>/dev/null || echo "Bucket may already exist"
fi

# Use existing AWS keys from .env or create new ones
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Creating access keys..."
    KEY_OUTPUT=$(yc iam access-key create --service-account-name "$SA_NAME" --format json-rest)
    export AWS_ACCESS_KEY_ID=$(echo "$KEY_OUTPUT" | grep -o '"key_id":"[^"]*"' | cut -d'"' -f4)
    export AWS_SECRET_ACCESS_KEY=$(echo "$KEY_OUTPUT" | grep -o '"secret":"[^"]*"' | cut -d'"' -f4)

    # Append to .env
    echo "" >> .env
    echo "# Auto-generated S3 keys" >> .env
    echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> .env
    echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env
fi

export S3_BUCKET=$BUCKET_NAME
echo -e "${GREEN}✅ Storage ready${NC}"

# ═══════════════════════════════════════════════════════════
# Step 4: Build Container
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}🔨 Building container...${NC}"

# Create Dockerfile if not exists
if [ ! -f "Dockerfile" ]; then
    cat > Dockerfile << 'DOCKERFILE_EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV DEBUG=false
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
EXPOSE 8080
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
DOCKERFILE_EOF
fi

docker build -t $IMAGE_NAME .
echo -e "${GREEN}✅ Built${NC}"

# ═══════════════════════════════════════════════════════════
# Step 5: Push to Registry
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}📤 Pushing to registry...${NC}"
docker push $IMAGE_NAME
echo -e "${GREEN}✅ Pushed${NC}"

# ═══════════════════════════════════════════════════════════
# Step 6: Deploy Serverless Container
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}🚀 Deploying container...${NC}"

# Create container if not exists
yc serverless container create --name $CONTAINER_NAME 2>/dev/null || true

# Build environment variables (simple string)
ENV_VARS="DEBUG=false,PORT=8080"
[ -n "$YDB_ENDPOINT" ] && ENV_VARS="$ENV_VARS,YDB_ENDPOINT=$YDB_ENDPOINT"
[ -n "$YDB_DATABASE" ] && ENV_VARS="$ENV_VARS,YDB_DATABASE=$YDB_DATABASE"
[ -n "$S3_BUCKET" ] && ENV_VARS="$ENV_VARS,S3_BUCKET=$S3_BUCKET"
[ -n "$AWS_ACCESS_KEY_ID" ] && ENV_VARS="$ENV_VARS,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
[ -n "$AWS_SECRET_ACCESS_KEY" ] && ENV_VARS="$ENV_VARS,AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
[ -n "$ELEVENLABS_API_KEY" ] && ENV_VARS="$ENV_VARS,ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY"
[ -n "$YAGPT_API_KEY" ] && ENV_VARS="$ENV_VARS,YAGPT_API_KEY=$YAGPT_API_KEY"
[ -n "$CLAUDE_API_KEY" ] && ENV_VARS="$ENV_VARS,CLAUDE_API_KEY=$CLAUDE_API_KEY"

# Deploy
yc serverless container revision deploy \
    --container-name $CONTAINER_NAME \
    --image $IMAGE_NAME \
    --cores 1 \
    --memory 512MB \
    --concurrency 4 \
    --execution-timeout 30s \
    --service-account-id $YC_SERVICE_ACCOUNT_ID \
    --environment "$ENV_VARS"

# Make public
yc serverless container allow-unauthenticated-invoke --name $CONTAINER_NAME 2>/dev/null || true

echo -e "${GREEN}✅ Deployed${NC}"

# ═══════════════════════════════════════════════════════════
# Step 7: Get URL and Health Check
# ═══════════════════════════════════════════════════════════
echo -e "${YELLOW}🔍 Getting container URL...${NC}"

# Get URL without jq
CONTAINER_URL=$(yc serverless container get $CONTAINER_NAME --format json-rest | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "🌐 Container URL: ${GREEN}$CONTAINER_URL${NC}"
echo -e "📊 YDB Database: ${GREEN}$DB_NAME${NC}"
echo -e "📦 S3 Bucket:    ${GREEN}$BUCKET_NAME${NC}"
echo ""
echo -e "${BLUE}Test endpoints:${NC}"
echo -e "curl $CONTAINER_URL/health"
echo -e "curl $CONTAINER_URL/"
echo ""

# Save deployment info
cat > .deploy_info << EOF
DEPLOY_URL=$CONTAINER_URL
CONTAINER_NAME=$CONTAINER_NAME
YDB_DATABASE=$YDB_DATABASE
S3_BUCKET=$BUCKET_NAME
DEPLOYED_AT=$(date)
EOF

echo -e "${GREEN}✅ Deployment info saved to .deploy_info${NC}"

# ═══════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════
echo ""
echo -e "${YELLOW}🏥 Running health check...${NC}"
sleep 10

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/health" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
elif [ "$HTTP_CODE" != "000" ]; then
    echo -e "${YELLOW}⚠ Container responding (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${YELLOW}⚠ Health check failed - container may still be starting${NC}"
    echo -e "   Check logs: yc logging read --group-id=\$(yc serverless container get $CONTAINER_NAME --format json-rest | grep -o '\"log_group_id\":\"[^\"]*\"' | cut -d'\"' -f4)"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Set up daily cron trigger (7:00 UTC):"
echo ""
echo "   yc serverless trigger create timer \\"
echo "       --name daily-podcast-generator \\"
echo "       --cron-expression \"0 7 * * ? *\" \\"
echo "       --invoke-container-name $CONTAINER_NAME \\"
echo "       --invoke-container-path /api/automation/generate \\"
echo "       --invoke-container-service-account-id $YC_SERVICE_ACCOUNT_ID"
echo ""
echo "2. View logs:"
echo ""
echo "   yc logging read --group-id=\$(yc serverless container get $CONTAINER_NAME --format json-rest | grep -o '\"log_group_id\":\"[^\"]*\"' | cut -d'\"' -f4) --follow"
echo ""
echo "3. Check status:"
echo ""
echo "   yc serverless container get $CONTAINER_NAME"
echo ""
