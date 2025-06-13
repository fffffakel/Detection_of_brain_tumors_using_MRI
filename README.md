# Detection of brain tumors using MRI

**Описание проекта:**
Автоматическое обнаружение опухолей головного мозга на МРТ-изображениях (.nii/.nii.gz) с помощью модели YOLO и фоновых задач через Celery.

**Команда разработки:**

* Новикова Полина: [Cabybariana](https://github.com/Capybariana)
* Георгий Каратеев: [zToasty](https://github.com/zToasty)
* Антон Шоколов: [fffffakel](https://github.com/fffffakel)

---

## Main

Обзор

Эта ветка реализует всю логику на CPU:

- Python API на Django для загрузки и предобработки МРТ.
- Интерфейс на Django (шаблоны + статика) для загрузки изображений и просмотра результатов.
- Docker / Docker Compose для контейнеризации.

### Требования

- **Python 3.8+**
- **pip**
- **Docker & Docker Compose** (Compose V2: команда `docker compose`)
- GPU/CUDA не требуются

### Установка и запуск

1. Клонировать и перейти в ветку CPU:

   ```bash
   git clone https://github.com/fffffakel/Detection_of_brain_tumors_using_MRI.git
   cd Detection_of_brain_tumors_using_MRI
   ```

2. Скопировать пример окружения и заполнить `.env` своими значениями:

   ```bash
   cp env.example .env
   ```

   ```dotenv
   # Secret key для Django
   SECRET_KEY=YOUR_SECRET_KEY_HERE

   # Настройки PostgreSQL
   POSTGRES_DB=YOUR_DB_NAME
   POSTGRES_USER=YOUR_DB_USER
   POSTGRES_PASSWORD=YOUR_DB_PASSWORD
   DATABASE_HOST=db
   DATABASE_PORT=5432


   # Django
   DEBUG=False

   # Redis / Celery
   REDIS_HOST=redis
   REDIS_PORT=6379
   CELERY_BROKER_URL=redis://redis:6379/0
   CELERY_RESULT_BACKEND=redis://redis:6379/0

   # Пути к модели
   BEST_MODEL_PATH=./yolo/best.pt
   YOLO_CONFIG_PATH=./yolo/best_model.txt

   ```

3. Инициализировать БД в файле init.sql своими значениями из .env (YOUR_DB_NAME, YOUR_DB_USER и YOUR_DB_PASSWORD):

   ```sql
   -- Инициализация базы данных (PostgreSQL)
   CREATE DATABASE IF NOT EXISTS YOUR_DB_NAME;
   CREATE USER YOUR_DB_USER WITH PASSWORD 'YOUR_DB_PASSWORD';
   ALTER ROLE YOUR_DB_USER SET client_encoding TO 'utf8';
   ALTER ROLE YOUR_DB_USER SET default_transaction_isolation TO 'read committed';
   ALTER ROLE YOUR_DB_USER SET timezone TO 'UTC';
   GRANT ALL PRIVILEGES ON DATABASE YOUR_DB_NAME TO YOUR_DB_USER;

   \connect YOUR_DB_NAME

   CREATE TABLE IF NOT EXISTS patients (
       id SERIAL PRIMARY KEY,
       name VARCHAR(255) NOT NULL,
       age INT CHECK (age >= 0),
       gender VARCHAR(10) CHECK (gender IN ('male','female','other')),
       doctor_name TEXT NOT NULL,
       doctor_diagnosis TEXT NOT NULL,
       neural_diagnosis TEXT NOT NULL,
       server_path TEXT NOT NULL
   );

   ```

4. Запуск приложения:

   - **В Docker**

     ```bash
     docker compose -f docker-compose-example.yml up --build

     ```

5. Переход к сайту:

   - **В любом браузере**

   [http://localhost:44444/](http://localhost:44444/)

---

## Структура файлов

```
Detection_of_brain_tumors_using_MRI/
├── .github/
│ └── workflows/ # CI/CD-конфигурации
├── BrainTumor/ # Код детекции опухолей: модели, скрипты, ноутбуки
├── WebSite/ # Исходники фронтенд-приложения
├── static/
│ └── WebSite/ # Статические файлы фронтенда
├── yolo/ # Интеграция и вспомогательные скрипты для YOLO-модели
├── .dockerignore # Правила игнорирования при сборке Docker-образа
├── .env # Переменные окружения 
├── .gitignore # Правила игнорирования Git
├── Dockerfile # Сборка Docker-образа для API
├── Dockerfile.celery # Сборка Docker-образа для Celery-воркера
├── celery_worker.sh # Скрипт запуска Celery-воркера
├── docker-compose.yml # Конфигурация Docker Compose для всех сервисов
├── entrypoint.sh # Точка входа в контейнеры
├── init.sql # SQL-скрипт инициализации БД
├── manage.py # Django-утилита управления проектом
└── requirements.txt # Python-зависимости
```

---

