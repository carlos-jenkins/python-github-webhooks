FROM python:3.7-alpine
#FROM python:3.7-slim

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000
CMD ["python3", "webhooks.py"]
