#syntax=docker/dockerfile:1

FROM python:3.10-slim AS builder

ARG INSTALL_RUST=false


WORKDIR /app

COPY . .

RUN sh <<'EOF'
    set -eu
    
    if [ "${INSTALL_RUST:-false}" = "true" ]; then
        apt-get update
        apt-get install -y --no-install-recommends curl build-essential
        curl https://sh.rustup.rs -sSf | sh -s -- -y
        . $HOME/.cargo/env
        rustup update
        rustup default stable
    fi
EOF

RUN sh <<'EOF'
    set -eu

    pip install uv
    uv venv -p ${PYTHON_VERSION}
    export OSTYPE=${OSTYPE:-linux-gnu}
    . .venv/bin/activate

    if [ "${INSTALL_RUST:-false}" = "true" ]; then
        . $HOME/.cargo/env
    fi

    if [ -f "pyproject.toml" ]; then
        uv pip install .
    else
        for dir in */; do
            if [ -f "$dir/pyproject.toml" ]; then
                uv pip install "$dir"
            fi
        done
    fi
EOF


FROM python:3.10-slim AS runtime

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8080

CMD ["bash", "-c", "source .venv/bin/activate && uvicorn src.nexus_tools.server.main:app --host 0.0.0.0 --port 8080"]
