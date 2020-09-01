ARG REGISTRY=eu.gcr.io/gcp-tooling-pro-eslm/github.com/adeo

# Get image from allinconfig--loader to get script for retrieving configuration
FROM $REGISTRY/allinconfig--loader:1.3.0-RC2 AS allinconfig--loader

FROM python:3.7-alpine

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

RUN apk add --update \
 curl \
 which \
 bash \
 unzip \
 jq \
 libxml2-utils 

RUN curl -sSL https://sdk.cloud.google.com | bash

ENV PATH $PATH:/root/google-cloud-sdk/bin

COPY . /app

RUN chmod +x /app/hooks/*

EXPOSE 5000

# Copy allinconfig modules to create environment from configuration (for serverless services)
COPY --from=allinconfig--loader /usr/local/bin/allinconfig /usr/local/bin/
ONBUILD ENV PATH="/usr/local/app/.venv/bin:$PATH"

CMD ["python3", "webhooks.py"]
