web: gunicorn inriver_qr.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py process_tasks
