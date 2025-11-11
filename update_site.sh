#!/bin/bash
# ============================
# Обновление Django проекта
# ============================

# ----------- Настройки проекта ------------
PROJECT_NAME="inriver_QR_generator_AWS"
PROJECT_DIR="/home/ubuntu/$PROJECT_NAME"
DJANGO_USER="django"
BRANCH="main"

# ----------- Переходим в директорию проекта ------------
echo "Переходим в директорию проекта..."
cd $PROJECT_DIR || { echo "Не удалось найти директорию $PROJECT_DIR"; exit 1; }

# ----------- Активируем виртуальное окружение ------------
echo "Активируем виртуальное окружение..."
source $PROJECT_DIR/venv/bin/activate

# ----------- Обновляем репозиторий ------------
echo "Получаем обновления из Git..."
git fetch origin $BRANCH
git reset --hard origin/$BRANCH

# ----------- Устанавливаем новые зависимости ------------
if [ -f "requirements.txt" ]; then
    echo "Устанавливаем зависимости..."
    pip install -r requirements.txt
fi

# ----------- Применяем миграции ------------
echo "Применяем миграции базы данных..."
python manage.py migrate

# ----------- Собираем статику ------------
echo "Собираем статику..."
python manage.py collectstatic --noinput

# ----------- Перезапуск Gunicorn через Supervisor ------------
echo "Перезапуск Gunicorn..."
sudo supervisorctl restart $PROJECT_NAME

echo "=========================================="
echo "Обновление проекта завершено!"
echo "Проверьте сайт: https://your_domain.com"
echo "=========================================="
