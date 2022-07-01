python -m venv venv

cd venv/Scripts

./activate

cd ..

pip install -r requirements.txt

python manage.py makemigrations

cd test_text

python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

------------------------------------

https://ckeditor.com/old/forums/CKEditor/Add-a-new-font - про то, как добавить стиль через venv.
Это получилось имплементировать

https://github.com/django-ckeditor/django-ckeditor/issues/404 - добавить стиль через static.
Один раз сработало - потом перестало

В админке пишите текст, используя тулзы необходимые, сохраняете объект

Далее можно достать все объекты по url http://127.0.0.1:8000/text_api/course/

Или какой-то один http://127.0.0.1:8000/text_api/course/{id}/




