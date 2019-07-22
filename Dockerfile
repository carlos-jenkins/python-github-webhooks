FROM python:2.7-alpine

WORKDIR /app

COPY config.json /app
COPY webhooks.py /app
COPY hooks /app/hooks
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

RUN chmod +x /app/hooks/*

EXPOSE 5000
CMD ["python", "webhooks.py"]
