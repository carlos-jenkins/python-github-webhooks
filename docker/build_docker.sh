#!/usr/bin/env bash

source docker/config_bash

git rev-parse HEAD >version

docker build --pull --tag=${IMAGE} --file=docker/Dockerfile .

rm version
