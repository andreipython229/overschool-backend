MANAGE = python manage.py
DOCKER_LOAD_DATA = docker-compose exec back python  overschool/manage.py loaddata
 # .PHONY defines parts of the makefile that are not dependant on any specific file
 .PHONY = run back test

 # Defining an array variable
 FILES = input output

 # Defines the default target that `make` will to try to make, or in the case of a phony target, execute the specified commands
 # This target is executed whenever we just type `make`
 .DEFAULT_GOAL = help

 # The @ makes sure that the command itself isn't echoed in the terminal
 help:
	@echo "---------------HELP-----------------"
	@echo "To run the project type make run"
	@echo "To load fixtures after running containers type make test"
	@echo "------------------------------------"

 run:
	sudo docker-compose up --build

 back:
	${MANAGE} collectstatic --noinput
	${MANAGE} makemigrations
	${MANAGE} migrate
	${MANAGE} migrate run_huey &
	daphne -b 0.0.0.0 -p 8000 overschool.asgi:application

	docker-compose exec back python overschool/manage.py test


 test:
#-----------------overschool-base/overschool/courses/fixtures------------------------------
	${DOCKER_LOAD_DATA}  test_initial_role_data.json
	${DOCKER_LOAD_DATA}  test_initial_tariff.json
	${DOCKER_LOAD_DATA}  test_initial_user_data.json
	${DOCKER_LOAD_DATA}  test_initial_school_data.json
	${DOCKER_LOAD_DATA}  test_initial_school_header.json
	${DOCKER_LOAD_DATA}  test_initial_course_data.json
	${DOCKER_LOAD_DATA}  test_initial_document_data.json
	${DOCKER_LOAD_DATA}  test_initial_section_data.json
	${DOCKER_LOAD_DATA}  test_initial_base_lesson_data.json
	${DOCKER_LOAD_DATA}  test_initial_students_group_settings.json
	${DOCKER_LOAD_DATA}  test_initial_students_group_data.json
	${DOCKER_LOAD_DATA}  test_initial_lesson_data.json
	${DOCKER_LOAD_DATA}  test_initial_homework_data.json
	${DOCKER_LOAD_DATA}  test_initial_data_section_test.json
	${DOCKER_LOAD_DATA}  test_initial_data_question.json
	${DOCKER_LOAD_DATA}  test_initial_data_answer.json
	${DOCKER_LOAD_DATA}  test_initial_user_homework_data.json
	${DOCKER_LOAD_DATA}  test_initial_data_user_test.json
	${DOCKER_LOAD_DATA}  test_initial_user_group_data.json
