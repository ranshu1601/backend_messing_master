FROM python:3.9.1-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

EXPOSE 80

CMD ["uvicorn", "asgi:app", "--host", "0.0.0.0", "--port", "8000"]
