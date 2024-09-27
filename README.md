## Тестовое задание

Для запуска при помощи docker `docker-compose up`

После запуска по адресу localhost:8000/docs будет доступно описание API

Сервис позовляет создавать задачи, прикреплять к ним изображения и анализировать лица на изображениях

### Настройки в env файле

Настройки БД:
```
DB_USER="postgres"
DB_HOST="postgres"
DB_NAME="tevian"
DB_PASS="postgres"
DB_PORT=5432
```

Настройка доступа к бэкенду анализатора лиц:
```
API_HOST="https://backend.facecloud.tevian.ru"
EMAIL="user@example.com"
PASSWORD="password"
```

Настройка Basic Auth:
```
LOCAL_LOGIN="admin"
LOCAL_PASSWORD="password"
```
