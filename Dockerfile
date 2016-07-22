FROM python:3.5.2-alpine
MAINTAINER "Matjaž Finžgar" <matjaz@finzgar.net>

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["python", "webhooks.py"]
