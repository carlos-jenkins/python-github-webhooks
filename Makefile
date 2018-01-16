docker-build-latest: docker-pull-deps
	docker build -t carlos-jenkins/python-github-webhooks .

docker-build-push: docker-build-latest
	TAG=$$(date +%Y%m%d%H%M%S) ;\
	docker tag carlos-jenkins/python-github-webhooks:latest carlos-jenkins/python-github-webhooks:$$TAG ; \
	docker push carlos-jenkins/python-github-webhooks:$$TAG ; \
	docker push carlos-jenkins/python-github-webhooks:latest ; \

docker-pull-deps:
	docker pull python:2.7-alpine

all: docker-build-latest
