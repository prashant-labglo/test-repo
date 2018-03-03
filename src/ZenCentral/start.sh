# Bash function to test if the input item is contained in the input list.
function list_include_item {
  local item="$1"
  local list="$2"
  if [[ $list =~ (^|[[:space:]])"$item"($|[[:space:]]) ]] ; then
    # yes, list include item
    result=0
  else
    result=1
  fi
  return $result
}

if [ "$HOSTNAME" != "preze-ntpc" ]
then
	python3 ./manage.py migrate
	python3 ./manage.py collectstatic
fi

# For most test machines.
if [ ! `list_include_item "$HOSTNAME" "lisa-dev lisa-prod"` ]
then
    if [[ ! -f apache/zenCentral.key ]] || [[ ! -f apache/zenCentral.crt ]]
    then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout apache/zenCentral.key -out apache/zenCentral.crt -subj \
	'/O=PREZENTIUM/OU=Tech/CN=www.prezentium.com'
    fi

fi

mkdir -p apache/logs
mod_wsgi-express module-config > apache/wsgi.conf
python3 ./manage.py createApacheSiteConf apache/site.conf
apache2 -d . -f apache/site.conf ;

