FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --target=/dependencies -r requirements.txt

COPY ./ .

#FROM gcr.io/distroless/python3
FROM python:3.11

WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /dependencies /dependencies


ENV PYTHONPATH=/dependencies
ENTRYPOINT ["python3", "collect.py"]

