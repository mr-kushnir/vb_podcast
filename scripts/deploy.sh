#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Deploy Script for Yandex Cloud
# Supports: Serverless Containers, YDB, Object Storage
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
TASK_ID="${2:-exam}"
VERSION="${3:-$(date +%Y%m%d-%H%M%S)}"

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}❌ .env file not found!${NC}"
    exit 1
fi

# Container name
CONTAINER_NAME="exam-$(echo $TASK_ID | tr '[:upper:]' '[:lower:]' | tr -d '-')"
IMAGE_NAME="cr.yandex/$YC_REGISTRY_ID/$CONTAINER_NAME:$VERSION"

# ═══════════════════════════════════════════════════════════
# Functions
# ═══════════════════════════════════════════════════════════

configure_yc() {
    echo -e "${BLUE}🔧 Configuring Yandex Cloud...${NC}"
    yc config set token $YC_TOKEN 2>/dev/null || true
    yc config set folder-id $YC_FOLDER_ID 2>/dev/null || true
    yc container registry configure-docker 2>/dev/null || true
}

# ─────────────────────────────────────────────────────────────
# YDB Functions
# ─────────────────────────────────────────────────────────────

setup_ydb() {
    echo -e "${YELLOW}📊 Setting up YDB...${NC}"
    
    DB_NAME="$CONTAINER_NAME-db"
    
    # Check if database exists
    DB_EXISTS=$(yc ydb database list --format json | jq -r ".[] | select(.name==\"$DB_NAME\") | .name")
    
    if [ -z "$DB_EXISTS" ]; then
        echo "Creating YDB database..."
        yc ydb database create \
            --name "$DB_NAME" \
            --serverless \
            --folder-id $YC_FOLDER_ID
        
        echo "Waiting for database to be ready..."
        sleep 10
    else
        echo "Database already exists"
    fi
    
    # Get connection info
    YDB_INFO=$(yc ydb database get "$DB_NAME" --format json)
    export YDB_ENDPOINT=$(echo $YDB_INFO | jq -r '.endpoint')
    export YDB_DATABASE=$(echo $YDB_INFO | jq -r '.database_path')
    
    echo -e "${GREEN}✅ YDB ready: $YDB_DATABASE${NC}"
    
    # Run migrations if exists
    if [ -f "migrations/tables.yql" ]; then
        echo "Running migrations..."
        yc ydb scripting yql \
            --database $YDB_DATABASE \
            --script-file migrations/tables.yql 2>/dev/null || true
    fi
}

# ─────────────────────────────────────────────────────────────
# Object Storage Functions
# ─────────────────────────────────────────────────────────────

setup_storage() {
    echo -e "${YELLOW}📦 Setting up Object Storage...${NC}"
    
    BUCKET_NAME="$CONTAINER_NAME-files"
    SA_NAME="$CONTAINER_NAME-sa"
    
    # Create service account if not exists
    SA_EXISTS=$(yc iam service-account list --format json | jq -r ".[] | select(.name==\"$SA_NAME\") | .id")
    
    if [ -z "$SA_EXISTS" ]; then
        echo "Creating service account..."
        yc iam service-account create --name "$SA_NAME"
        
        SA_ID=$(yc iam service-account get "$SA_NAME" --format json | jq -r '.id')
        
        # Grant permissions
        yc resource-manager folder add-access-binding $YC_FOLDER_ID \
            --role storage.editor \
            --subject serviceAccount:$SA_ID 2>/dev/null || true
        yc resource-manager folder add-access-binding $YC_FOLDER_ID \
            --role ydb.editor \
            --subject serviceAccount:$SA_ID 2>/dev/null || true
        yc resource-manager folder add-access-binding $YC_FOLDER_ID \
            --role serverless.containers.invoker \
            --subject serviceAccount:$SA_ID 2>/dev/null || true
            
        export YC_SERVICE_ACCOUNT_ID=$SA_ID
    else
        export YC_SERVICE_ACCOUNT_ID=$SA_EXISTS
    fi
    
    # Check if bucket exists
    BUCKET_EXISTS=$(yc storage bucket list --format json 2>/dev/null | jq -r ".[] | select(.name==\"$BUCKET_NAME\") | .name")
    
    if [ -z "$BUCKET_EXISTS" ]; then
        echo "Creating bucket..."
        yc storage bucket create \
            --name $BUCKET_NAME \
            --default-storage-class standard \
            --max-size 1073741824 2>/dev/null || true
    else
        echo "Bucket already exists"
    fi
    
    # Create access keys if needed
    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        echo "Creating access keys..."
        KEY_INFO=$(yc iam access-key create --service-account-name "$SA_NAME" --format json)
        export AWS_ACCESS_KEY_ID=$(echo $KEY_INFO | jq -r '.access_key.key_id')
        export AWS_SECRET_ACCESS_KEY=$(echo $KEY_INFO | jq -r '.secret')
        
        echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" >> .env
        echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" >> .env
    fi
    
    export S3_BUCKET=$BUCKET_NAME
    
    echo -e "${GREEN}✅ Storage ready: $BUCKET_NAME${NC}"
}

# ─────────────────────────────────────────────────────────────
# Container Functions
# ─────────────────────────────────────────────────────────────

build_container() {
    echo -e "${YELLOW}🔨 Building container...${NC}"
    
    # Create Dockerfile if not exists
    if [ ! -f "Dockerfile" ]; then
        cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
EOF
    fi
    
    docker build -t $IMAGE_NAME .
    echo -e "${GREEN}✅ Built: $IMAGE_NAME${NC}"
}

push_container() {
    echo -e "${YELLOW}📤 Pushing to registry...${NC}"
    docker push $IMAGE_NAME
    echo -e "${GREEN}✅ Pushed: $IMAGE_NAME${NC}"
}

deploy_container() {
    echo -e "${YELLOW}🚀 Deploying Serverless Container...${NC}"
    
    # Create container if not exists
    yc serverless container create --name $CONTAINER_NAME 2>/dev/null || true
    
    # Build environment
    ENV_VARS="BOT_TOKEN=${BOT_TOKEN:-}"
    [ -n "$YDB_ENDPOINT" ] && ENV_VARS="$ENV_VARS,YDB_ENDPOINT=$YDB_ENDPOINT"
    [ -n "$YDB_DATABASE" ] && ENV_VARS="$ENV_VARS,YDB_DATABASE=$YDB_DATABASE"
    [ -n "$S3_BUCKET" ] && ENV_VARS="$ENV_VARS,S3_BUCKET=$S3_BUCKET"
    [ -n "$AWS_ACCESS_KEY_ID" ] && ENV_VARS="$ENV_VARS,AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID"
    [ -n "$AWS_SECRET_ACCESS_KEY" ] && ENV_VARS="$ENV_VARS,AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY"
    
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
    
    CONTAINER_URL=$(yc serverless container get $CONTAINER_NAME --format json | jq -r '.url')
    echo "DEPLOY_URL=$CONTAINER_URL" > .deploy_info
    
    echo -e "${GREEN}✅ Deployed: $CONTAINER_URL${NC}"
}

health_check() {
    echo -e "${YELLOW}🏥 Health check...${NC}"
    
    CONTAINER_URL=$(yc serverless container get $CONTAINER_NAME --format json | jq -r '.url')
    sleep 5
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/health" 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Healthy${NC}"
        return 0
    else
        # Try root
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$CONTAINER_URL/" 2>/dev/null || echo "000")
        if [ "$HTTP_CODE" != "000" ]; then
            echo -e "${YELLOW}⚠ Container responding (HTTP $HTTP_CODE)${NC}"
            return 0
        fi
        echo -e "${RED}❌ Failed${NC}"
        return 1
    fi
}

setup_webhook() {
    [ -z "$BOT_TOKEN" ] && return 0
    
    echo -e "${YELLOW}🔗 Setting webhook...${NC}"
    CONTAINER_URL=$(yc serverless container get $CONTAINER_NAME --format json | jq -r '.url')
    
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/setWebhook" \
        -H "Content-Type: application/json" \
        -d "{\"url\": \"$CONTAINER_URL/webhook\"}" > /dev/null
    
    echo -e "${GREEN}✅ Webhook: $CONTAINER_URL/webhook${NC}"
}

rollback() {
    echo -e "${YELLOW}⏪ Rolling back...${NC}"
    
    PREV=$(yc serverless container revision list --container-name $CONTAINER_NAME --format json | jq -r '.[1].id')
    
    if [ -n "$PREV" ] && [ "$PREV" != "null" ]; then
        yc serverless container rollback --container-name $CONTAINER_NAME --revision-id $PREV
        echo -e "${GREEN}✅ Rolled back${NC}"
    else
        echo -e "${RED}❌ No previous revision${NC}"
    fi
}

status() {
    echo -e "${BLUE}📊 Status${NC}"
    
    # Container
    URL=$(yc serverless container get $CONTAINER_NAME --format json 2>/dev/null | jq -r '.url')
    [ -n "$URL" ] && echo -e "Container: ${GREEN}$URL${NC}"
    
    # YDB
    YDB=$(yc ydb database get "$CONTAINER_NAME-db" --format json 2>/dev/null | jq -r '.status')
    [ -n "$YDB" ] && echo -e "YDB: ${GREEN}$YDB${NC}"
    
    # Storage
    S3=$(yc storage bucket list --format json 2>/dev/null | jq -r ".[] | select(.name==\"$CONTAINER_NAME-files\") | .name")
    [ -n "$S3" ] && echo -e "S3: ${GREEN}$S3${NC}"
}

full_deploy() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🚀 Deploying: $CONTAINER_NAME${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    
    configure_yc
    setup_ydb
    setup_storage
    build_container
    push_container
    deploy_container
    
    if health_check; then
        setup_webhook
        
        CONTAINER_URL=$(yc serverless container get $CONTAINER_NAME --format json | jq -r '.url')
        
        echo ""
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ DEPLOYED${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "🌐 URL: ${GREEN}$CONTAINER_URL${NC}"
        echo -e "📊 YDB: ${GREEN}$CONTAINER_NAME-db${NC}"
        echo -e "📦 S3:  ${GREEN}$CONTAINER_NAME-files${NC}"
    else
        echo -e "${RED}Deploy failed, rolling back...${NC}"
        rollback
        exit 1
    fi
}

# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

case $COMMAND in
    deploy|full)  full_deploy ;;
    build)        build_container ;;
    push)         push_container ;;
    container)    configure_yc && deploy_container ;;
    ydb)          configure_yc && setup_ydb ;;
    storage|s3)   configure_yc && setup_storage ;;
    health)       health_check ;;
    webhook)      setup_webhook ;;
    rollback)     configure_yc && rollback ;;
    status)       configure_yc && status ;;
    *)
        echo "Usage: $0 {deploy|build|push|container|ydb|storage|health|webhook|rollback|status} [task_id] [version]"
        exit 1
        ;;
esac
