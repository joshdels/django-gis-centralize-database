djlint . --reformat && \
python manage.py tailwind build &&  \
python manage.py collectstatic --no-input --clear &&  \
cp theme/static/css/dist/styles.css static/css/dist/styles.css && \
python manage.py runserver 