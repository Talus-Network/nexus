python_version := "3.10"
llama_version := "llama3.2:1b"
sui_tag := "testnet-v1.28.3"

[private]
default:
    @just -l

# Commands for running examples
mod example 'examples/example.just'

# Installs `uv`.
uv-setup:
    #!/usr/bin/env bash
    set -eu

    # See: https://github.com/astral-sh/uv
    if ! command -v uv; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi

    uv --version

# Installs python using `uv`.
python-setup: uv-setup
    #!/usr/bin/env bash
    set -eu
    export RUST_LOG=warn

    uv python install {{ python_version }}

# Creates a `.venv` and installs all the dependencies.
venv-setup: python-setup
    #!/usr/bin/env bash
    set -eu
    export RUST_LOG=warn

    # Create the venv
    uv venv -p {{ python_version }}

    # Install everything
    uv pip install ./nexus_sdk/
    uv pip install ./offchain/events
    uv pip install ./offchain/tools

    uv pip install -r ./examples/requirements.txt


# lightweight check to see if .venv exists, instead of using `venv-setup`
[private]
venv-exists:
    @test -d .venv || (echo "Please run 'just venv-setup' first" && exit 1)

# Starts a ptpython shell with the `.venv` activated.
python-shell: venv-exists
    #!/usr/bin/env bash
    source .venv/bin/activate
    ptpython

# Installs ollama.
ollama-setup:
    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull {{ llama_version }}

# Installs OS-level dependencies.
apt-setup:
    #!/usr/bin/env bash

    # These should already be installed ...
    sudo apt install -y git-all curl wget python3

    sudo apt install -y cmake libssl-dev pkg-config lsof

# below is from christos PR (https://github.com/Talus-Network/protochain/pull/19):
# Installs `suibase` and sets up `localnet`.
suibase-setup:
    #!/usr/bin/env bash
    set -euo pipefail

    # Suibase installs everything in ~/.local/bin.
    # So this must be in the PATH.
    # We abort if it is not because other scripts depend on it.
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo '======================================='
        echo 'ERROR: ~/.local/bin is NOT in your PATH'
        echo 'Suibase installs everything in ~/.local/bin and heavily relies on it.'
        echo 'Please add it to your PATH and try again.'
        echo '======================================='
        exit 1
    fi

    # install suibase
    if [[ ! -d ~/suibase ]]; then
        echo Installing suibase
        echo
        git clone https://github.com/sui-base/suibase.git ~/suibase
        cd ~/suibase
        ./install

        localnet create
        # Pin Sui version to minimum supported by Suibase.
        # This ought to match the talus package version as close as possible.
        config=~/suibase/workdirs/localnet/suibase.yaml
        echo '' >> $config
        echo 'force_tag: "{{ sui_tag }}"' >> $config
        localnet update
    else
        echo ~/suibase exists
    fi

# Starts LLM and other tools in an uvicorn server on port 8080.
start-tools:
    #!/usr/bin/env bash
    source .venv/bin/activate
    uvicorn offchain.tools.src.nexus_tools.server.main:app --host 0.0.0.0 --port 8080

# Starts Sui event listener that invokes tools and submits completions.
# See `offchain/events` for more information about flags/envs.
start-events +args:
    #!/usr/bin/env bash
    source .venv/bin/activate
    python3 offchain/events/src/nexus_events/sui_event.py {{args}}

############################################
## devnet
############################################
# Sets up `devnet` (which is `localnet` from suibase)
devnet-setup: suibase-setup
  echo
  type lsui localnet
  localnet set-active

devnet-status: devnet-setup
  echo
  localnet status
  echo
  localnet links || true

devnet-start: devnet-setup
    #!/usr/bin/env bash
    echo
    RUST_LOG=warn localnet start






