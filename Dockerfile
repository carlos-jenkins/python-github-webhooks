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
 jq

RUN curl -sSL https://sdk.cloud.google.com | bash

ENV PATH $PATH:/root/google-cloud-sdk/bin

COPY webhooks.py /app
RUN mkdir /app/hooks
COPY hooks/* /app/hooks
COPY cloudbuild.yaml /app/

RUN chmod +x /app/hooks/*

EXPOSE 5000
CMD ["python", "webhooks.py"]
