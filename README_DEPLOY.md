# 🚀 Quick Deploy Guide

## Для быстрого деплоя на Yandex Cloud

### 1. Установка Yandex Cloud CLI (один раз)

```bash
# На Linux/WSL
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Перезагрузить shell или
source ~/.bashrc

# Проверить
yc --version
```

### 2. Настройка

```bash
# Инициализация (использует YC_TOKEN из .env)
yc init --token $YC_TOKEN

# Или ввести токен вручную
yc init

# Установить folder
yc config set folder-id $YC_FOLDER_ID

# Настроить Docker registry
yc container registry configure-docker
```

### 3. Быстрый деплой (БЕЗ jq)

```bash
# Сделать скрипт исполняемым
chmod +x scripts/deploy_simple.sh

# Запустить деплой
./scripts/deploy_simple.sh deploy pod vb-podcast
```

Скрипт автоматически:
- ✅ Создаст YDB базу данных
- ✅ Настроит S3 хранилище
- ✅ Соберет Docker образ
- ✅ Загрузит в Container Registry
- ✅ Развернет Serverless Container
- ✅ Проверит здоровье приложения
- ✅ Покажет URL и команды для настройки

### 4. После деплоя

```bash
# URL сохранен в .deploy_info
cat .deploy_info

# Проверить работу
curl $(grep DEPLOY_URL .deploy_info | cut -d'=' -f2)/health

# Посмотреть логи
yc logging read --group-id=$(yc serverless container get exam-podvbpodcast --format json-rest | grep -o '"log_group_id":"[^"]*"' | cut -d'"' -f4) --follow
```

## Настройка автоматической генерации (cron)

После успешного деплоя скрипт покажет команду для настройки. Пример:

```bash
# Генерация подкастов каждый день в 7:00 UTC
yc serverless trigger create timer \
    --name daily-podcast-generator \
    --cron-expression "0 7 * * ? *" \
    --invoke-container-name exam-podvbpodcast \
    --invoke-container-path /api/automation/generate \
    --invoke-container-service-account-id <your-service-account-id>
```

## Требования

### Обязательно:
- ✅ Yandex Cloud CLI
- ✅ Docker
- ✅ .env файл с YC_TOKEN и YC_FOLDER_ID

### НЕ требуется:
- ❌ jq (скрипт работает без него)
- ❌ дополнительные инструменты

## Проблемы?

### Docker не найден
```bash
# Ubuntu/Debian
sudo apt-get install docker.io

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### YC CLI не найден
```bash
# Проверить установку
which yc

# Если не найден, переустановить
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
source ~/.bashrc
```

### Ошибка доступа к registry
```bash
# Перенастроить Docker
yc container registry configure-docker

# Проверить авторизацию
docker login cr.yandex
```

## Полная документация

См.: [DEPLOYMENT.md](./DEPLOYMENT.md)

## Стоимость

~$5-7/месяц за:
- Serverless Container (512MB RAM, 1 core)
- YDB Serverless (4 таблицы)
- S3 Storage (1GB аудио)

## Альтернативный скрипт (с jq)

Если у вас установлен jq, можно использовать расширенный скрипт:

```bash
./scripts/deploy.sh deploy pod vb-podcast
```

Он имеет больше функций (status, rollback, отдельные команды для YDB/S3).
