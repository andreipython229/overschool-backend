MANAGE = python manage.py
DOCKER_TEST = docker compose exec back python  overschool/manage.py
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
	sudo docker compose up --build

 back:  
	${MANAGE} makemigrations
	${MANAGE} migrate 
	${MANAGE} runserver 0.0.0.0:8000

 test:
	${DOCKER_TEST} loaddata initial_role_data.json
	${DOCKER_TEST} loaddata test_document_data.json
	${DOCKER_TEST} loaddata test_user_initial_data.json
	${DOCKER_TEST} loaddata test_profile_initial_data.json
	${DOCKER_TEST} loaddata test_initial_course_data.json
	${DOCKER_TEST} loaddata test_initial_section_data.json
	${DOCKER_TEST} loaddata test_initial_lesson_data.json
	${DOCKER_TEST} loaddata test_initial_user_progress_data.json
	${DOCKER_TEST} loaddata test_initial_homework_data.json
	${DOCKER_TEST} loaddata test_initial_user_homework_data.json
	${DOCKER_TEST} loaddata test_initial_data_lesson_test.json
	${DOCKER_TEST} loaddata test_initial_data_question.json
	${DOCKER_TEST} loaddata test_initial_data_answer.json
	${DOCKER_TEST} loaddata test_initial_data_user_test.json
	${DOCKER_TEST} loaddata test_initial_students_group_data.json





