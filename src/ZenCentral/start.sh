if [ "$HOSTNAME" != "preze-ntpc" ]
then
	python3 ./manage.py migrate
	python3 ./manage.py collectstatic
fi

mkdir -p apache/logs
mod_wsgi-express module-config > apache/wsgi.conf
python3 ./manage.py createApacheSiteConf apache/site.conf
apache2 -d . -f apache/site.conf ;

