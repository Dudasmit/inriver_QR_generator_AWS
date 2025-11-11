#!/bin/bash
# =============================================
# Автоматизация развёртывания Django + Celery на Ubuntu
# =============================================

PROJECT_NAME="inriver_QR_generator_AWS"
PROJECT_DIR="/home/ubuntu/$PROJECT_NAME"
GIT_REPO="git@github.com:Dudasmit/inriver_QR_generator_AWS.git"
DJANGO_USER="ubuntu"
DOMAIN="tikhonovskyi.com"
PYTHON_VERSION="3.12"
WSGI_MODULE="inriver_qr.wsgi:application"
CELERY_APP_MODULE="inriver_qr.celery_app:app"

echo "Обновление системы..."
sudo apt update -y && sudo apt upgrade -y

echo "Установка пакетов..."
sudo apt install -y python3-pip python3-venv python3-dev git nginx curl ufw \
    certbot python3-certbot-nginx postgresql postgresql-contrib redis-server

echo "Настройка директории проекта..."
sudo -u $DJANGO_USER mkdir -p $PROJECT_DIR

if [ ! -d "$PROJECT_DIR/.git" ]; then
    sudo -u $DJANGO_USER git clone $GIT_REPO $PROJECT_DIR
else
    cd $PROJECT_DIR && sudo -u $DJANGO_USER git pull
fi

echo "Создаём виртуальное окружение..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    sudo -u $DJANGO_USER python3 -m venv $PROJECT_DIR/venv
fi

sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt

echo "Применяем миграции и собираем статику..."
sudo -u $DJANGO_USER bash -c "source $PROJECT_DIR/venv/bin/activate && \
    python $PROJECT_DIR/manage.py migrate && \
    python $PROJECT_DIR/manage.py collectstatic --noinput"

# ----------- Gunicorn systemd ------------
echo "Настройка Gunicorn..."
GUNICORN_SERVICE_FILE="/etc/systemd/system/gunicorn.service"
cat > $GUNICORN_SERVICE_FILE <<EOL
[Unit]
Description=Gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$DJANGO_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=DEBUG=False
Environment=SECRET_KEY=<ваш секретный ключ>
Environment=ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
Environment=DB_NAME=postgres
Environment=DB_USER=postgres
Environment=DB_PASSWORD=<ваш пароль>
Environment=DB_HOST=localhost
Environment=DB_PORT=5432
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock $WSGI_MODULE

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn

# ----------- Celery worker systemd ------------
echo "Настройка Celery worker..."
CELERY_SERVICE_FILE="/etc/systemd/system/celery.service"
cat > $CELERY_SERVICE_FILE <<EOL
[Unit]
Description=Celery Worker for $PROJECT_NAME
After=network.target

[Service]
Type=forking
User=$DJANGO_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment=CELERY_BROKER_URL=redis://localhost:6379/0
Environment=CELERY_RESULT_BACKEND=redis://localhost:6379/0
ExecStart=$PROJECT_DIR/venv/bin/celery -A $CELERY_APP_MODULE multi start worker --loglevel=info --pidfile=/tmp/celery_%n.pid
ExecStop=$PROJECT_DIR/venv/bin/celery -A $CELERY_APP_MODULE multi stopwait worker --pidfile=/tmp/celery_%n.pid
ExecReload=$PROJECT_DIR/venv/bin/celery -A $CELERY_APP_MODULE multi restart worker --loglevel=info --pidfile=/tmp/celery_%n.pid

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable celery
sudo systemctl start celery

# ----------- Nginx ------------
echo "Настройка Nginx..."
NGINX_CONF="/etc/nginx/sites-available/$PROJECT_NAME"
cat > $NGINX_CONF <<EOL
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $PROJECT_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/$PROJECT_NAME.sock;
    }
}
EOL

ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "Настройка HTTPS через Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true

echo "Настройка UFW..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "=========================================="
echo "✅ Деплой завершён! Провер
