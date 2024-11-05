#!/bin/sh

if [ "$INSTALL_RUST" = "true" ]; then
    exit 1
    apt-get update 
    apt-get install -y --no-install-recommends curl build-essential
    curl https://sh.rustup.rs -sSf | sh -s -- -y
    . $HOME/.cargo/env
    rustup update
    rustup default stable
fi

pip install uv
uv venv -p "$PYTHON_VERSION"
export OSTYPE=${OSTYPE:-linux-gnu}
. .venv/bin/activate

if [ "$INSTALL_RUST" = "true" ]; then
    exit 1
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
