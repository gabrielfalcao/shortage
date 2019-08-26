# prepare toolbelt to run in test-mode
current_dir := $(shell pwd)
export PYTHONDONTWRITEBYTECODE	:= yes
DOCKER_RUN	:= source .env && docker run -t -i -v $$HOME/.shortage/data:/srv/data -e TWILIO_AUTH_TOKEN -e TWILIO_ACCOUNT_SID gabrielfalcao/shortage
POETRY_RUN	:= source .env && poetry run
HTTP_REQUEST	:= curl -v -X POST -H "Content-Type: application/json" -d @.request.json
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
	$(POETRY_RUN) flake8 --ignore=E501 shortage tests docs/source/conf.py

black: # format all python code with black
	$(POETRY_RUN) black --line-length 79 shortage tests

develop: # install all development dependencies with poetry
	poetry install
	$(POETRY_RUN) python setup.py develop

docker: docker-image docker-push

docker-image:
	time docker build -t gabrielfalcao/shortage .

docker-push:
	docker push gabrielfalcao/shortage

docker-run:
	$(DOCKER_RUN)

docker-shell:
	$(DOCKER_RUN) bash

tests:  # run unit and functional tests together aggregating total coverage
	$(POETRY_RUN) nosetests tests --cover-erase

tests-with-timer:  # run all tests with time tracking (nice for seeing slow ones)
	$(POETRY_RUN) nosetests tests --cover-erase --with-timer

unit:   # run unit tests, erases coverage file
	$(POETRY_RUN) nosetests tests/$@ --cover-erase # let's clear the test coverage report during unit tests only

functional: # run functional tests
	$(POETRY_RUN) nosetests tests/$@

tdd-unit:  # run unit tests in watch mode
	$(POETRY_RUN) nosetests --with-watch tests/unit

tdd-functional:  # run functional tests in watch mode
	$(POETRY_RUN) nosetests --with-watch tests/functional/

tdd:  # run all tests in watch mode (nice for top-down tdd)
	$(POETRY_RUN) nosetests --with-watch tests/

run:
	$(POETRY_RUN) shortage web

run-debug:
	$(POETRY_RUN) shortage web --debug

local-request:
	$(HTTP_REQUEST) http://localhost:3000/sms/in
	@echo

request:
	$(HTTP_REQUEST) https://sms.falcao.it/sms/in
	@echo

remote-request: request


docs-html: # (re) generates documentation
	$(POETRY_RUN) make -C docs html

docs: docs-html  # (re) generates documentation and open in browser
	open docs/build/html/index.html

clean:  # remove temporary files including byte-compiled python files
	@rm -rf shortage/docs *egg-info* .noseids
	@find . -type d -path '*/shortage/*/__pycache__' -or -path '*/tests/*/__pycache__' | xargs rm -rf

# tells "make" that the target "make docs" is phony, meaning that make
# should ignore the existence of a file or folder named "docs" and
# simply execute commands described in the target
.PHONY: docs black tests shortage operations dist build
