# Simple Dockerfile for running the demo
FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install -e .[dev]
ENTRYPOINT ["spectral-discovery"]
