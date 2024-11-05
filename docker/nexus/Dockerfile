#syntax=docker/dockerfile:1

FROM python:3.10-slim AS builder

ARG INSTALL_RUST=false

ENV INSTALL_RUST=${INSTALL_RUST}

WORKDIR /app

RUN ls -lta

COPY . .

COPY --from=nexus bin/setup_venv.sh /usr/local/bin/setup_venv.sh

RUN chmod +x /usr/local/bin/setup_venv.sh

RUN /usr/local/bin/setup_venv.sh

FROM python:3.10-slim AS runtime

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8080

CMD ["bash", "-c", "source .venv/bin/activate && uvicorn src.nexus_tools.server.main:app --host 0.0.0.0 --port 8080"]
