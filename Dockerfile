FROM python:2.7-alpine

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt
RUN apk add --update \
 python \
 curl \
 which \
 bash \
 unzip

RUN curl -sSL https://sdk.cloud.google.com | bash

ENV PATH $PATH:/root/google-cloud-sdk/bin

COPY . /app

RUN chmod +x /app/hooks/*

EXPOSE 5000
CMD ["python", "webhooks.py"]
