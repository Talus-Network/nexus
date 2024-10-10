# Stage 1: Build environment
FROM ubuntu:22.04 as build-env

# Environment variables
ARG PYTHON_VERSION="3.10"
ARG SUI_TAG="testnet-v1.29.1"

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    cmake \
    libssl-dev \
    pkg-config \
    lsof \
    build-essential \
    sudo \
    bash \
    vim

# Create a non-root user 'sui'
RUN useradd -ms /bin/bash sui

# Switch to non-root user 'sui'
USER sui

# Set HOME environment variable for 'sui'
ENV HOME /home/sui
WORKDIR /home/sui

# Ensure ~/.local/bin is in PATH for non-root user
ENV PATH="${PATH}:/home/sui/.local/bin"

# Install Rust (required for uv) as non-root user
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    . $HOME/.cargo/env && rustup update

# Install Just command runner
RUN curl -sSf https://just.systems/install.sh | bash -s -- --to /home/sui/.local/bin/

# Install uv (for managing Python environments)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install Suibase as non-root user
RUN git clone https://github.com/sui-base/suibase.git /home/sui/suibase && \
    cd /home/sui/suibase && ./install 

RUN localnet create

RUN config="/home/sui/suibase/workdirs/localnet/suibase.yaml" && \
    sed -i '/^force_tag:/d' $config && \
    echo "force_tag: \"${SUI_TAG}\"" >> $config

RUN . $HOME/.cargo/env && /home/sui/.local/bin/localnet update

# Stage 2: Application environment setup
FROM ubuntu:22.04 as runtime-env

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    cmake \
    libssl-dev \
    pkg-config \
    lsof \
    build-essential \
    bash

# Create non-root user 'sui' in runtime
RUN useradd -ms /bin/bash sui

# Copy files from the build stage
COPY --from=build-env /home/sui/.local/bin/just /usr/local/bin/just
COPY --from=build-env /home/sui/.cargo /home/sui/.cargo
COPY --from=build-env /home/sui/.cargo/bin/uv /usr/local/bin/uv
COPY --from=build-env /home/sui/suibase /home/sui/suibase
COPY --from=build-env /home/sui/.local/bin /home/sui/.local/bin

# Ensure ~/.local/bin is in PATH for non-root user
ENV PATH="${PATH}:/home/sui/.local/bin:/home/sui/.cargo/bin"
RUN rustup default stable
RUN chown -R sui:sui /home/sui/

# Switch to non-root user 'sui'
USER sui
WORKDIR /home/sui

ARG PYTHON_VERSION="3.10"
ENV PYTHON_VERSION=${PYTHON_VERSION}

# Install Python 3.10 using uv and create venv
RUN uv python install ${PYTHON_VERSION} && \
    uv venv -p ${PYTHON_VERSION}

USER root
# Copy project files
COPY ./nexus_sdk/ ./nexus_sdk/
RUN chown -R sui:sui /home/sui/nexus_sdk/
COPY ./offchain/events/ ./offchain/events/
COPY ./offchain/tools/ ./offchain/tools/
RUN chown -R sui:sui /home/sui/offchain/
COPY ./examples/requirements.txt ./examples/
RUN chown -R sui:sui /home/sui/examples/

USER sui
# Install Python dependencies inside the virtual environment
RUN bash -c "source .venv/bin/activate && \
    rustup default stable && \
    uv pip install ./nexus_sdk/ && \
    uv pip install ./offchain/events && \
    uv pip install ./offchain/tools && \
    uv pip install -r ./examples/requirements.txt"

# Expose necessary ports for the tools
EXPOSE 8080

# Start the uvicorn server and any other services
CMD ["bash", "-c", "source .venv/bin/activate && uvicorn offchain.tools.src.nexus_tools.server.main:app --host 0.0.0.0 --port 8080"]
