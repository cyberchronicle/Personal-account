# check if we have .env file and load it
ifneq ("$(wildcard .env)","")
    include .env
    export
endif

POSTGRES_SETUP_TEST := user=${POSTGRES_USER} password=${POSTGRES_PASSWORD} dbname=${POSTGRES_DB} host=${POSTGRES_HOST} port=${POSTGRES_PORT} sslmode=disable
MIGRATION_FOLDER=$(CURDIR)/migrations

.PHONY: pip-install
pip-install:
	pip install -r requirements.txt

.PHONY: docker
docker:
	docker-compose up -d --build

.PHONY: fastapi
fastapi:
	python3 -m uvicorn --app-dir ./app/ main:app --reload --host 0.0.0.0 --port 8001

.PHONY: minio
minio:
	docker-compose up minio -d --build

.PHONY: migration-create
migration-create:
	goose -dir "$(MIGRATION_FOLDER)" create "$(name)" sql

.PHONY: migration-up
migration-up:
	goose -dir "$(MIGRATION_FOLDER)" postgres "$(POSTGRES_SETUP_TEST)" up

.PHONY: migration-down
migration-down:
	goose -dir "$(MIGRATION_FOLDER)" postgres "$(POSTGRES_SETUP_TEST)" down

