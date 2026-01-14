# 🚀 Quick Deploy Guide

## Для быстрого деплоя на Yandex Cloud

### 1. Установка инструментов (один раз)

```bash
# На Linux/WSL
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
sudo apt-get install jq docker.io

# Настройка YC CLI
yc init --token $YC_TOKEN
yc config set folder-id $YC_FOLDER_ID
yc container registry configure-docker
```

### 2. Быстрый деплой

```bash
# Сделать скрипт исполняемым
chmod +x scripts/deploy.sh

# Запустить полный деплой
./scripts/deploy.sh deploy pod vb-podcast
```

Скрипт автоматически:
- ✅ Создаст YDB базу данных
- ✅ Настроит S3 хранилище
- ✅ Соберет Docker образ
- ✅ Загрузит в Container Registry
- ✅ Развернет Serverless Container
- ✅ Проверит здоровье приложения

### 3. Получить URL

```bash
yc serverless container get exam-podvbpodcast --format json | jq -r '.url'
```

### 4. Проверить работу

```bash
# Health check
curl https://ваш-url.apigw.yandexcloud.net/health

# API
curl https://ваш-url.apigw.yandexcloud.net/
```

## Настройка автоматической генерации (cron)

```bash
# Генерация подкастов каждый день в 7:00 UTC
yc serverless trigger create timer \
    --name daily-podcast \
    --cron-expression "0 7 * * ? *" \
    --invoke-container-name exam-podvbpodcast \
    --invoke-container-path /api/automation/generate \
    --invoke-container-service-account-id $YC_SERVICE_ACCOUNT_ID
```

## Проблемы?

См. полную документацию: [DEPLOYMENT.md](./DEPLOYMENT.md)

## Стоимость

~$5-7/месяц за:
- Serverless Container
- YDB (Serverless)
- S3 Storage (1GB)
