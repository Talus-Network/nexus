#!/usr/bin/env bash

#
# The purpose of this bash script is to run the end-to-end tests for the Talus
# package in the localnet environment with one command.
#
# The script assumes:
# - sui CLI, jq, cargo
# - env var SUI_WALLET_PATH pointing to the wallet yaml
#   or it can be alternatively defined in .env file (see README)
# - pwd is a git repo
#
# 1. Assert that dependencies are installed
# 2. Assert that the script is run from the correct directory
# 3. Start sui _localnet_ node in the background
# 4. Wait for sui RPC to be available
# 5. Publish the Talus package to the sui node and get its package ID
# 6. Run the E2E tests against the published package but with mocked ollama
# 7. Kill the sui node
#
# This script has been tested on Ubuntu 22.04.
#

#
# 1.
#

sui --version
if [ $? -ne 0 ]; then
    echo "Sui CLI is not installed"
    exit 1
fi
jq --version
if [ $? -ne 0 ]; then
    echo "jq is not installed"
    exit 1
fi
cargo --version
if [ $? -ne 0 ]; then
    echo "cargo is not installed"
    exit 1
fi

#
# 2.
#

# get the root dir, assuming we are under a git repo structure
root_dir=$(git rev-parse --show-toplevel)
if [ $? -ne 0 ]; then
    echo "Not in a git repo"
    exit 1
fi
pkg_path="${root_dir}/onchain"
e2e_path="${root_dir}/e2e_tests"

if [ ! -d "$pkg_path" ]; then
    echo "Talus package path ${pkg_path} does not exist"
    exit 1
fi
if [ ! -d "$e2e_path" ]; then
    echo "E2E Rust tests path ${e2e_path} does not exist"
    exit 1
fi

#
# 3.
#

# assert that active env is localnet
# we assume that you have set it up, e.g. using `sui genesis`
# we first run 'sui client active-env' which prompts the user to create an
# environment if it doesn't exist yet
echo "Expecting active environment to be localnet at http://localhost:9000"
sui client active-env || exit 1
active_env=$(sui client active-env </dev/null)
if [ "$active_env" != "localnet" ]; then
    echo "Active environment is not localnet"
    echo "You can change the active environment in the client config yaml"
    exit 1
fi

nohup sui start >sui.log 2>&1 &
sui_pid=$! # will be used to kill sui process later
kill_sui_localnet() {
    echo "Killing sui node"
    kill $sui_pid
}

# handle Control-C, which is can be useful when running the script interactively
trap 'kill_sui_localnet' INT

#
# 4.
#

echo "Waiting for sui to start"
# retry sui client balance 10 times with 2 second delay until it succeeds
# or exit if it fails after 10 retries
max_retries=10
for i in $(seq 1 $max_retries); do
    balance=$(sui client balance)
    if [ $? -eq 0 ]; then
        break
    fi
    if [ $i -eq $max_retries ]; then
        echo "Failed to start sui."
        echo "Try 'sui start' and see what might be the issue."
        echo "You need 'sui genesis' if you haven't started the localnet yet"
        # send exit signal just in case
        kill_sui_localnet
        exit 1
    fi
    sleep 2
done

# kill the sui node if the tests fail
trap 'kill_sui_localnet' ERR

#
# 5.
#

echo "Publishing package"
cd $pkg_path
json=$(sui client publish --skip-dependency-verification --json)
if [ $? -ne 0 ]; then
    echo "Failed to publish package:"
    echo
    echo
    echo $json
    exit 1
fi

fw_pkg_id=$(echo $json | jq -cr '.objectChanges[] | select(.packageId) | .packageId')
# assert fw_pkg_id starts with 0x as a valid object ID
if [[ ! $fw_pkg_id =~ ^0x ]]; then
    echo "Invalid package ID: ${fw_pkg_id}"
    exit 1
fi

#
# 6.
#

echo "Running E2E tests"
cd $e2e_path
# start with mocked ollama
FW_PKG_ID="${fw_pkg_id}" \
    OLLAMA_HTTP_API="" \
    RUST_LOG="info" \
    cargo run
if [ $? -ne 0 ]; then
    echo "E2E tests failed"
    exit 1
fi

#
# 7.
#

kill_sui_localnet
