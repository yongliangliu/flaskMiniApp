sudo kill -9 $(ps -ef|grep gunicorn |gawk '$0 !~/grep/ {print $2}' |tr -s '/n' ' ')
sudo gunicorn -c gun.py pythonService:app
