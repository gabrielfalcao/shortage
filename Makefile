# prepare toolbelt to run in test-mode
current_dir := $(shell pwd)
export PYTHONDONTWRITEBYTECODE	:= yes
DOCKER_RUN	:= source .env && docker run -t -i -v $$HOME/.shortage/data:/srv/data -e TWILIO_AUTH_TOKEN -e TWILIO_ACCOUNT_SID gabrielfalcao/shortage

# NOTE: the first target of a makefile executed when ``make`` is
# executed without arguments.
# It was deliberately named "default" here but could be any name.
# Also feel free to modify it to execute a custom command.
#
#
default: recreate develop tests docs


recreate: clean  # destroys virtualenv, create new virtualenv and install all python dependencies
	rm -rf .venv poetry.lock
	make dependencies

dependencies: # install and configure poetry, create new virtualenv and install python dependencies
	pip3 install -q -U poetry --no-cache-dir --user
	poetry config settings.virtualenvs.in-project true
	make develop

lint: # run flake8
	poetry run flake8 --ignore=E501 shortage tests docs/source/conf.py

black: # format all python code with black
	poetry run black --line-length 79 shortage tests

develop: # install all development dependencies with poetry
	poetry install
	poetry run python setup.py develop

docker-image:
	time docker build -t gabrielfalcao/shortage .

docker-push:
	docker push gabrielfalcao/shortage

docker-run:
	$(DOCKER_RUN)

docker-shell:
	$(DOCKER_RUN) bash

tests:  # run unit and functional tests together aggregating total coverage
	poetry run nosetests tests --cover-erase

tests-with-timer:  # run all tests with time tracking (nice for seeing slow ones)
	poetry run nosetests tests --cover-erase --with-timer

unit:   # run unit tests, erases coverage file
	poetry run nosetests tests/$@ --cover-erase # let's clear the test coverage report during unit tests only

functional: # run functional tests
	poetry run nosetests tests/$@

tdd-unit:  # run unit tests in watch mode
	poetry run nosetests --with-watch tests/unit

tdd-functional:  # run functional tests in watch mode
	poetry run nosetests --with-watch tests/functional/

tdd:  # run all tests in watch mode (nice for top-down tdd)
	poetry run nosetests --with-watch tests/

run:
	poetry run shortage web

run-debug:
	poetry run shortage web --debug

request-local:
	curl -X POST -H "Content-Type: application/json" -d @.request.json http://localhost:3000/sms/in

request-remote:
	curl -X POST -H "Content-Type: application/json" -d @.request.json https://sms.falcao.it/sms/in

docs-html: # (re) generates documentation
	poetry run make -C docs html

docs: docs-html  # (re) generates documentation and open in browser
	open docs/build/html/index.html

clean:  # remove temporary files including byte-compiled python files
	@rm -rf shortage/docs *egg-info* .noseids
	@find . -type d -path '*/shortage/*/__pycache__' -or -path '*/tests/*/__pycache__' | xargs rm -rf

# tells "make" that the target "make docs" is phony, meaning that make
# should ignore the existence of a file or folder named "docs" and
# simply execute commands described in the target
.PHONY: docs black tests shortage operations dist build
