FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN python3.12 -m venv venv
RUN ./venv/bin/pip install --upgrade pip && ./venv/bin/pip install -r requirements.txt

EXPOSE 80

CMD ["./venv/bin/gunicorn", "--bind", "0.0.0.0:80", "app:app"]
