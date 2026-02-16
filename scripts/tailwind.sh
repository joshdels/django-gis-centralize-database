python manage.py tailwind build &&  \
python manage.py collectstatic --no-input --clear &&  \
cp staticfiles/css/dist/styles.css static/css/dist/styles.css && \
python manage.py runserver 