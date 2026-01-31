FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

COPY carelink-lib/client.py .
COPY carelink-lib/client_proxy.py .

# CMD ["python", "/app/client_proxy.py"]
ENTRYPOINT ["python", "/app/client_proxy.py"]
