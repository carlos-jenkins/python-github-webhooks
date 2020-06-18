ARG REGISTRY=eu.gcr.io/gcp-tooling-pro-eslm/github.com/adeo

# Get image from allinconfig--loader to get script for retrieving configuration
FROM $REGISTRY/allinconfig/allinconfig--loader-python3.7:latest AS allinconfig--loader

FROM python:2.7-alpine

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

RUN apk add --update \
 python \
 curl \
 which \
 bash \
 unzip \
 jq \
 python3 \
 libxml2-utils \
 py3-yaml && \
 pip3 install kubernetes 

RUN curl -s https://storage.googleapis.com/berglas/master/linux_amd64/berglas --output /usr/local/bin/berglas && chmod +x /usr/local/bin/berglas

RUN curl -sSL https://sdk.cloud.google.com | bash

ENV PATH $PATH:/root/google-cloud-sdk/bin

COPY . /app

RUN chmod +x /app/hooks/*

EXPOSE 5000

# Copy allinconfig modules to create environment from configuration (for serverless services)
COPY --from=allinconfig--loader /usr/local/app/ /usr/local/app/
ONBUILD ENV PATH="/usr/local/app/.venv/bin:$PATH"

CMD ["python", "webhooks.py"]
