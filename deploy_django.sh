#!/bin/bash
# =============================================
# Автоматизация развёртывания Django на Azure
# =============================================

# ----------- Настройки проекта ------------
PROJECT_NAME="inriver_QR_generator_AWS"
PROJECT_DIR="/home/ubuntu/$PROJECT_NAME"
GIT_REPO="git@github.com:Dudasmit/inriver_QR_generator_AWS.git"
DJANGO_USER="ubuntu"
DOMAIN="tikhonovskyi.com"
PYTHON_VERSION="3.12"
WSGI_MODULE="inriver_qr.wsgi:application"

# ----------- Обновление системы ------------
echo "Обновление системы..."
sudo apt update -y && sudo apt upgrade -y

# ----------- Установка необходимых пакетов ------------
echo "Установка пакетов..."
sudo apt install -y python3-pip python3-venv python3-dev git nginx curl ufw certbot python3-certbot-nginx postgresql postgresql-contrib

# ----------- Настройка проекта ------------
echo "Настройка директории проекта..."
sudo -u $DJANGO_USER mkdir -p $PROJECT_DIR

if [ ! -d "$PROJECT_DIR/.git" ]; then
    sudo -u $DJANGO_USER git clone $GIT_REPO $PROJECT_DIR
else
    cd $PROJECT_DIR && sudo -u $DJANGO_USER git pull
fi

# ----------- Виртуальное окружение ------------
echo "Создаём виртуальное окружение..."
if [ ! -d "$PROJECT_DIR/venv" ]; then
    sudo -u $DJANGO_USER python3 -m venv $PROJECT_DIR/venv
fi

sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt

# ----------- Создание .env при необходимости ------------
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo "Создаём .env..."
    cat <<EOL | sudo tee $PROJECT_DIR/.env > /dev/null
DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_HOST=localhost
DB_PORT=5432
EOL
    sudo chown $DJANGO_USER:$DJANGO_USER $PROJECT_DIR/.env
fi

# ----------- Миграции и сборка статики ------------
echo "Применяем миграции и собираем статику..."
sudo -u $DJANGO_USER bash -c "source $PROJECT_DIR/venv/bin/activate && \
    python $PROJECT_DIR/manage.py migrate && \
    python $PROJECT_DIR/manage.py collectstatic --noinput"

# ----------- Настройка Gunicorn через systemd ------------
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
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock $WSGI_MODULE

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl restart gunicorn

# ----------- Настройка Nginx ------------
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

# ----------- Настройка HTTPS ------------
echo "Настройка HTTPS через Let's Encrypt..."
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN || true

# ----------- Настройка брандмауэра ------------
echo "Настройка UFW..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "=========================================="
echo "✅ Деплой завершён! Проверьте сайт на https://$DOMAIN"
echo "Для обновления: зайдите в $PROJECT_DIR и выполните git pull + migrate + collectstatic"
echo "=========================================="
