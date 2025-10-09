release: python manage.py migrate profiles 0003 --fake
release: python manage.py migrate
web: gunicorn fitness_portal.wsgi:application