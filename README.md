# Functionality

Retrieve list of products from inriver.
Get the name and barcode of each item.
Formation of QR code, with the possibility of adding a barcode.
Before forming a link to the QR code there is a check for the existence of the link, for example: https://www.esschertdesign.com/qr/XM82.

## Uploading to the server

sudo apt get update
sudo apt-get install -y git python3-dev python3-venv python3-pip supervisor nginx vim libpq-dev
git clone https://github.com/Dudasmit/django-QR-generator.git
cd django-QR-generator
python3 -m venv venv   
source venv/bin/activate
pip3 install -r requirements.txt 

cd inriver_qr
python3 manage.py makemigrations
python3 manage.py migrate

python3 manage.py collectstatic

python3 manage.py runserver 0.0.0.0:8000



### Fixed problems:

update git :
git pull https://github.com/Dudasmit/django-QR-generator.git

in case of error:
Error: That port is already in use.
ps aux | grep manage

root          89  0.0  0.0      0     0 ?        I<   07:07   0:00 [kworker/R-charger_manager]
dudasmit    4267  0.0  1.1  55788 46108 pts/0    T    09:16   0:00 python3 manage.py runserver 0.0.0.0:8000
dudasmit    4268  0.3  1.6 372152 67888 pts/0    Tl   09:16   0:01 /home/dudasmit/django-QR-generator/venv/bin/python3 manage.py runserver 0.0.0.0:8000
dudasmit    4338  0.0  0.0   4180  2196 pts/0    S+   09:22   0:00 grep --color=auto manage   

kill -9 4267



#### Fixed problems:




heroku login
heroku container:login
heroku create your-app-name







Запустите Docker Desktop вручную

heroku container:login

heroku stack:set container --app inriverqr



heroku container:push web --app inriverqr
heroku container:release web --app inriverqr

heroku run python manage.py migrate --app inriverqr
heroku run python manage.py makemigrations --app inriverqr


heroku run python manage.py createsuperuser --app inriverqr
heroku open --app inriverqr


heroku logs --tail --app inriverqr





docker run -it inriverqr /bin/bash

python manage.py migrate

heroku ps:scale worker=1



python manage.py runserver 0.0.0.0:8000
exit


#worker: python manage.py process_tasks

Запустить
heroku ps:scale worker=1 --app inriverqr 
остановить 
heroku ps:scale worker=0 --app inriverqr


Проверка статуса dyno:
bash
Копировать
Редактировать
heroku ps --app inriverqr