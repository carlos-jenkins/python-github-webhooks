FROM python:2.7-alpine
MAINTAINER "Matjaž Finžgar" <matjaz@finzgar.net>

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "webhooks.py"]
