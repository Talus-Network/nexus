#
# This script accepts one argument: the name of the example to run.
#
# Available examples:
# - trip_planner
# - ig_post_planner
# - cli_cluster
#
# ```bash
# python main.py ${EXAMPLE_NAME}
# ```
#
# # Requirements
#
# - Suibase "localnet" CLI
# - Nexus SDK installed
# - `offchain/tools` installed
# - `offchain/events` installed
#
# # Steps
#
# This script prepares all resources necessary to run an example.
# 1. Starts localnet with Suibase
# 2. Publishes the talus package
# 3. Gets the Sui keypair from the environment and airdrops SUI
# 4. Creates a node and a model
# 5. Asks the user to Talus services
# 6. Runs the example that the user selected

import json
import os
import re
import subprocess
import sys
from cli_cluster import run_cli_cluster_example
from colorama import init as colorama_init
from ig_post_planner import run_ig_post_planner_example
from nexus_sdk import get_sui_client, create_node, create_model
from pathlib import Path
from trip_planner import run_trip_planner_example

# we know that this script is located in the ./examples directory, so we go
# one level up to get the root directory of the repository
repo_root_dir = Path(__file__).resolve().parent.parent


# Maps example name to a function that runs it.
# In essence, this is the source of truth for supported examples.
EXAMPLES = {
    "trip_planner": run_trip_planner_example,
    "ig_post_planner": run_ig_post_planner_example,
    "cli_cluster": run_cli_cluster_example,
}


def main():
    colorama_init()

    example_name = sys.argv[1]
    if example_name not in EXAMPLES:
        raise ValueError(
            f"Unknown example name: {example_name}. Available examples: {EXAMPLES.keys()}"
        )

    # 1.
    print("Starting localnet...")
    start_localnet()

    # 2.
    print("Publishing Talus package...")
    package_id = publish_talus_package()

    # 3.
    print("Preparing Sui address...")
    sui_address = get_sui_address()
    airdrop_sui(sui_address)
    private_key = get_sui_address_private_key(sui_address)
    client = get_sui_client(private_key)

    # 4.
    print("Creating node and model...")
    node_id = create_example_node(client, package_id)
    llama_id, llama_owner_cap_id = create_llama_model(client, package_id, node_id)

    # 5.
    ask_user_to_start_talus_services(private_key, package_id, llama_owner_cap_id)

    # 6.
    try:
        print()
        EXAMPLES[example_name](client, package_id, llama_id, llama_owner_cap_id)
        print()
        print(f"Example {example_name} finished")
    except Exception as e:
        print(f"Failed to run example {example_name}: {e}")


def start_localnet():
    run_command("localnet start")

    status_output = run_command("localnet status")

    # "OK" is printed in green color, so we cannot do a simple string comparison
    ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
    clean_status_output = ansi_escape.sub("", status_output)
    if "localnet OK" not in clean_status_output:
        print()
        print("Output of localnet status:")
        print(status_output)
        raise Exception("Failed to start localnet. Try `$ localnet regen`")


# Assumes localnet being started and Suibase installed in the default path.
def publish_talus_package():
    # TODO: https://github.com/Talus-Network/TAF/issues/9
    run_command(
        "localnet publish --skip-dependency-verification",
        cwd=repo_root_dir / "onchain",
    )

    package_id = None
    published_data_path = os.path.expanduser(
        "~/suibase/workdirs/localnet/published-data/talus/most-recent/package-id.json"
    )
    if not os.path.exists(published_data_path):
        raise FileNotFoundError(
            f"Published data file not found at {published_data_path}. Please ensure the Talus package has been published."
        )
    with open(published_data_path) as f:
        data = json.load(f)
        if not data:
            raise ValueError(
                "Published data file is empty. Please check your Talus package publication."
            )
        package_id = data[0]

    if not package_id:
        raise ValueError("Failed to extract PACKAGE_ID from the published data file.")

    return package_id


# Uses the suibase CLI to get the currently active address
def get_sui_address():
    return run_command("lsui client active-address").strip()


# Airdrops some SUI to the localnet faucet address and returns the address.
def airdrop_sui(address):
    # trims whitespaces and new lines
    run_command(f"localnet faucet {address}")


# Reads the private key for the given address from the Sui keystore.
def get_sui_address_private_key(for_address):
    all_addresses_json = run_command("lsui client addresses --json")
    # Find the position of the address in the list of .addresses.
    # Each address is a two-element list: [method, public_key]
    all_addresses = json.loads(all_addresses_json)
    position = None
    for i, [_, address] in enumerate(all_addresses["addresses"]):
        if address == for_address:
            position = i
            break

    if position is None:
        raise ValueError(f"Address '{for_address}' not found in client addresses")

    keystore_path = os.path.expanduser(
        "~/suibase/workdirs/localnet/config/sui.keystore"
    )
    if not os.path.exists(keystore_path):
        raise FileNotFoundError(
            f"Sui client file not found at {keystore_path}. Please ensure Sui is properly set up."
        )

    with open(keystore_path) as f:
        keys = json.load(f)
        if not keys:
            raise ValueError(
                "Sui keystore file is empty. Please check your Sui configuration."
            )
        return keys[position]


# Creates a new node owned object.
def create_example_node(client, package_id):
    node_id = create_node(client, package_id, "LocalNode", "CPU", 16)
    if not node_id:
        raise Exception("Failed to create node")

    return node_id


# Creates llama model representation on chain.
#
# Returns the model ID and the model owner capability ID.
def create_llama_model(client, package_id, node_id):
    model_id, model_owner_cap_id = create_model(
        client=client,
        package_id=package_id,
        node_id=node_id,
        name="llama3.2:1b",
        model_hash=b"llama3.2_1b_hash",
        url="http://localhost:11434",
        token_price=1000,
        capacity=1000000,
        num_params=1000000000,
        description="llama3.2 1b",
        max_context_length=8192,
        is_fine_tuned=False,
        family="Llama3.2",
        vendor="Meta",
        is_open_source=True,
        datasets=["test"],
    )
    if not model_id:
        raise Exception("Failed to create model")

    return model_id, model_owner_cap_id


# Prints how to start Talus services.
def ask_user_to_start_talus_services(private_key, package_id, model_owner_cap_id):
    print()
    print("You need to start the Talus services.")
    print("Open a new terminal for both the LLM Assistant and the Event Listener.")
    print()

    # check if something is running on port 8080
    llm_assistant_cmd = f"""
        just start-tools
    """
    print("First you need to start the LLM assistant unless it's running already.")
    print("Start the LLM Assistant with the following command:")
    print(llm_assistant_cmd)

    input("Press enter when ready...")
    print()

    inferenced_cmd = f"""
        just start-events \\
            --packageid {package_id} \\
            --privkey {private_key} \\
            --modelownercapid {model_owner_cap_id}
    """
    print(
        "Next, let's start the Event Listener for this example with the following command:"
    )
    print()
    print(inferenced_cmd)

    input("Press enter when ready...")


# Runs given command and returns the output.
def run_command(command, cwd=None):
    result = subprocess.run(
        command, cwd=cwd, shell=True, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error executing command: {command}")
        print(f"Error output: {result.stdout}\n\n{result.stderr}")
        raise Exception(f"Command failed: {command}")
    return result.stdout


if __name__ == "__main__":
    main()
