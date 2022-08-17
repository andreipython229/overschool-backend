echo "кто мечтает быть пилотом?
очень смелый видно тот
потому что только смелый
сам полезет в самолет
потому что только смелых уважает высота
потому что в самолете все зависит от ......"
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata initial_role_data.json
python manage.py loaddata test_document_data.json
python manage.py loaddata test_user_initial_data.json
python manage.py loaddata test_profile_initial_data.json
python manage.py loaddata test_initial_course_data.json
python manage.py loaddata test_initial_section_data.json
python manage.py loaddata test_initial_lesson_data.json
python manage.py loaddata test_initial_user_progress_data.json
python manage.py loaddata test_initial_homework_data.json
python manage.py loaddata test_initial_user_homework_data.json
python manage.py loaddata test_initial_data_lesson_test.json
python manage.py loaddata test_initial_data_question.json
python manage.py loaddata test_initial_data_answer.json
python manage.py loaddata test_initial_data_user_test.json
python manage.py loaddata test_initial_stidents_group_data.json
python manage.py runserver 0.0.0.0:8000