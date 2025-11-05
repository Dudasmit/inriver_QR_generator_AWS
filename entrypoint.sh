#!/bin/sh

# Применяем миграции
#echo "==> Running migrations..."
#python manage.py migrate --noinput

# Собираем статику (можно закомментировать при локальной разработке)
echo "==> Collecting static files..."
#python manage.py collectstatic --noinput --verbosity=2
python manage.py process_tasks &

# Запускаем сервер
echo "==> Starting gunicorn..."
exec gunicorn inriver_qr.wsgi:application --bind 0.0.0.0:$PORT --timeout 800
