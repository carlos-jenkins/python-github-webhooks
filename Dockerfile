FROM python:2.7-alpine
MAINTAINER "Matjaž Finžgar" <matjaz@finzgar.net>

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=3", "wsgi"]
