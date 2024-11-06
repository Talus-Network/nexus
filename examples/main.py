import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from cli_cluster import run_cli_cluster_example
from colorama import init as colorama_init
from ig_post_planner import run_ig_post_planner_example
from trip_planner import run_trip_planner_example
from nexus_sdk import get_sui_client

# We know that this script is located in the ./examples directory, so we go
# one level up to get the root directory of the repository
repo_root_dir = Path(__file__).resolve().parent.parent

# Define paths to shared resources
shared_dir = Path(os.getenv("SHARED_DIR", "."))
keystore_path = Path(shared_dir) / "sui.keystore"
package_id_path = Path(shared_dir) / "package_id.json"
node_details_path = Path(shared_dir) / "node_details.json"

rpc_url = os.getenv("RPC_URL", "http://localhost:9000")
ws_url = os.getenv("WS_URL", "ws://localhost:9000")

# Maps example name to a function that runs it.
# In essence, this is the source of truth for supported examples.
EXAMPLES = {
    "trip_planner": run_trip_planner_example,
    "ig_post_planner": run_ig_post_planner_example,
    "cli_cluster": run_cli_cluster_example,
}


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


def load_configuration():
    """Load the required configuration from predefined paths."""
    # Load package ID
    try:
        with open(package_id_path, "r") as f:
            package_id = json.load(f)[0]
    except (FileNotFoundError, IndexError, json.JSONDecodeError) as e:
        print(f"Error: Unable to load package ID from {package_id_path}. Details: {e}")
        sys.exit(1)

    # Load node details
    try:
        with open(node_details_path, "r") as f:
            node_details = json.load(f)
            llama_id = node_details.get("llama_id")
            llama_owner_cap_id = node_details.get("llama_owner_cap_id")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(
            f"Error: Unable to load node details from {node_details_path}. Details: {e}"
        )
        sys.exit(1)

    if not llama_id or not llama_owner_cap_id:
        print("Error: Llama ID or Llama Owner Capability ID is missing.")
        sys.exit(1)

    # Load SUI private key from keystore JSON
    try:
        with open(keystore_path, "r") as f:
            keys = json.load(f)
            if not keys:
                raise ValueError(
                    "Sui keystore file is empty. Please check your Sui configuration."
                )
            private_key = keys[0]  # Assuming the first key is used
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(
            f"Error: Unable to load SUI private key from {keystore_path}. Details: {e}"
        )
        sys.exit(1)

    return package_id, llama_id, llama_owner_cap_id, private_key


def main():
    colorama_init()

    # Argument parsing
    parser = argparse.ArgumentParser(
        description="Run a specific example with Sui client."
    )
    parser.add_argument(
        "example_name",
        help="The name of the example to run. Available examples: trip_planner, ig_post_planner, cli_cluster",
    )
    args = parser.parse_args()

    # Validate the example name
    example_name = args.example_name
    if example_name not in EXAMPLES:
        raise ValueError(
            f"Unknown example name: {example_name}. Available examples: {list(EXAMPLES.keys())}"
        )

    # Load configuration from known paths
    package_id, llama_id, llama_owner_cap_id, private_key = load_configuration()
    # Create the Sui client

    client = get_sui_client(private_key, rpc_url=rpc_url, ws_url=ws_url)
    # Run the selected example
    try:
        print(f"\nRunning example: {example_name}\n")
        EXAMPLES[example_name](client, package_id, llama_id, llama_owner_cap_id)
        print(f"\nExample {example_name} finished successfully.")
    except Exception as e:
        print(f"Failed to run example {example_name}: {e}")


if __name__ == "__main__":
    main()
