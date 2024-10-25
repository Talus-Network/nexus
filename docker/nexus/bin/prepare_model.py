# Import necessary modules
import json
from pathlib import Path
from nexus_sdk import get_sui_client, create_node, create_model
import os

# Decoupled function to create node and model and save details to a file.
def create_and_save_node_and_model(client, package_id):
    node_id = create_example_node(client, package_id)
    llama_id, llama_owner_cap_id = create_llama_model(client, package_id, node_id)

    # Save the node details to a JSON file
    shared_dir = Path("/app/shared")
    shared_dir.mkdir(parents=True, exist_ok=True)
    node_details = {
        "node_id": node_id,
        "llama_id": llama_id,
        "llama_owner_cap_id": llama_owner_cap_id,
    }
    with open(shared_dir / "node_details.json", "w") as f:
        json.dump(node_details, f, indent=4)

    return node_id, llama_id, llama_owner_cap_id

# Creates a new node owned object.
def create_example_node(client, package_id):
    node_id = create_node(client, package_id, "LocalNode", "CPU", 16)
    if not node_id:
        raise Exception("Failed to create node")
    return node_id

# Creates llama model representation on chain.
# Returns the model ID and the model owner capability ID.
def create_llama_model(client, package_id, node_id):
    model_id, model_owner_cap_id = create_model(
        client=client,
        package_id=package_id,
        node_id=node_id,
        name="llama3.2:1b",
        model_hash=b"llama3.2_1b_hash",
        url=os.getenv("MODEL_URL", "http://localhost:11434"),
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

if __name__ == "__main__":
    # Example usage:
    # Initialize client and package_id appropriately before running this script
    keystore_path = Path("/app/sui.keystore")
    with open(keystore_path, "r") as f:
        keys = json.load(f)
        if not keys:
            raise ValueError("Sui keystore file is empty. Please check your Sui configuration.")
        private_key = keys[0]  # Assuming the first key is used
    rpc_url = os.getenv("RPC_URL", "http://localhost:9000")
    ws_url = os.getenv("WS_URL", "ws://localhost:9000")
    client = get_sui_client(private_key, rpc_url=rpc_url, ws_url=ws_url)


    package_id_file = Path("/app/shared/package-id.json")
    with open(package_id_file, "r") as f:
        package_id_list = json.load(f)
        package_id = package_id_list[0]
    create_and_save_node_and_model(client, package_id)
    print("environment prepared successfully")