FROM python:3.10-slim AS builder

ARG INSTALL_RUST=false

WORKDIR /app

COPY . .

RUN if [ "$INSTALL_RUST" = "true" ]; then \
        apt-get update && apt-get install -y --no-install-recommends curl build-essential && \ 
        curl https://sh.rustup.rs -sSf | sh -s -- -y && \
        . $HOME/.cargo/env && \ 
        rustup update && \
        rustup default stable; \
    fi

RUN pip install uv && \
    uv venv -p ${PYTHON_VERSION} && \
    . .venv/bin/activate && \
    if [ "$INSTALL_RUST" = "true" ]; then \
        . $HOME/.cargo/env; \
    fi && \
    uv pip install . 

FROM python:3.10-slim AS runtime

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8080

CMD ["bash", "-c", "source .venv/bin/activate && uvicorn src.nexus_tools.server.main:app --host 0.0.0.0 --port 8080"]
