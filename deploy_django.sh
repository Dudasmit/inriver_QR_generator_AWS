#!/bin/bash
# =============================================
# Автоматизация развёртывания Django на Azure
# =============================================

# ----------- Настройки проекта ------------
PROJECT_NAME="inriver_QR_generator_AWS"
PROJECT_DIR="/home/ubuntu/$PROJECT_NAME"
GIT_REPO="git@github.com:username/inriver_QR_generator_AWS.git"
DJANGO_USER="django"
DOMAIN="tikhonovskyi.com"
PYTHON_VERSION="3.11"
wsgiPROJECT_NAME="inriver_qr"

# ----------- Обновление системы ------------
echo "Обновление системы..."
apt update && apt upgrade -y

# ----------- Установка необходимых пакетов ------------
echo "Установка пакетов..."
apt install -y python3-pip python3-dev python3-venv git nginx curl ufw supervisor certbot python3-certbot-nginx

# ----------- Создание пользователя ------------
if ! id -u $DJANGO_USER >/dev/null 2>&1; then
    echo "Создаём пользователя $DJANGO_USER..."
    adduser --disabled-password --gecos "" $DJANGO_USER
    usermod -aG sudo $DJANGO_USER
fi

# ----------- Настройка директории проекта ------------
echo "Настройка директории проекта..."
sudo -u $DJANGO_USER mkdir -p $PROJECT_DIR
sudo -u $DJANGO_USER git clone $GIT_REPO $PROJECT_DIR || (cd $PROJECT_DIR && sudo -u $DJANGO_USER git pull)

# ----------- Создание виртуального окружения ------------
echo "Создаём виртуальное окружение..."
sudo -u $DJANGO_USER python3 -m venv $PROJECT_DIR/venv
sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $DJANGO_USER $PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt

# ----------- Миграции и сборка статики ------------
echo "Применяем миграции и собираем статику..."
sudo -u $DJANGO_USER bash -c "source $PROJECT_DIR/venv/bin/activate && python $PROJECT_DIR/manage.py migrate && python $PROJECT_DIR/manage.py collectstatic --noinput"

# ----------- Настройка Gunicorn ------------
echo "Настройка Gunicorn..."
GUNICORN_SERVICE_FILE="/etc/systemd/system/gunicorn.service"
cat > $GUNICORN_SERVICE_FILE <<EOL
[Unit]
Description=gunicorn daemon for $PROJECT_NAME
After=network.target

[Service]
User=$DJANGO_USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock $wsgiPROJECT_NAME.wsgi:application

[Install]
WantedBy=multi-user.target
EOL

systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn

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
nginx -t && systemctl restart nginx

# ----------- Настройка HTTPS ------------
echo "Настройка HTTPS через Let's Encrypt..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

# ----------- Настройка Supervisor ------------
echo "Настройка Supervisor..."
SUPERVISOR_CONF="/etc/supervisor/conf.d/$PROJECT_NAME.conf"
cat > $SUPERVISOR_CONF <<EOL
[program:$PROJECT_NAME]
directory=$PROJECT_DIR
command=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/$PROJECT_NAME.sock $PROJECT_NAME.wsgi:application
autostart=true
autorestart=true
stderr_logfile=/var/log/$PROJECT_NAME.err.log
stdout_logfile=/var/log/$PROJECT_NAME.out.log
user=$DJANGO_USER
group=www-data
EOL

supervisorctl reread
supervisorctl update
supervisorctl restart $PROJECT_NAME

# ----------- Настройка брандмауэра ------------
echo "Настройка UFW..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "=========================================="
echo "Деплой завершён! Проверьте сайт на https://$DOMAIN"
echo "Для обновления: зайдите в $PROJECT_DIR и выполните git pull + миграции + collectstatic"
echo "=========================================="
