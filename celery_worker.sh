#!/bin/bash
echo "Запуск Celery worker..."
exec celery -A BrainTumor worker --loglevel=info
