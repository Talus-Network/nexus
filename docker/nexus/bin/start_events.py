import os
import json
import subprocess
from pathlib import Path

# Set paths
shared_dir = Path(os.getenv('SHARED_DIR', '.'))
keystore_path = Path(shared_dir) / "sui.keystore"

# Extract details from JSON files
package_id_path = Path(shared_dir) / "package-id.json"
node_details_path = Path(shared_dir) / "node_details.json"


rpc_url = os.getenv('RPC_URL', 'http://localhost:9000')
ws_url = os.getenv('WS_URL', 'ws://localhost:9000')
tool_url = os.getenv('TOOL_URL', 'http://0.0.0.0:8080/tool/use')

# Load package ID
try:
    with open(package_id_path, 'r') as f:
        package_id = json.load(f)[0]
except (FileNotFoundError, IndexError, json.JSONDecodeError) as e:
    print(f"Error: Unable to load package ID from {package_id_path}. Details: {e}")
    exit(1)

# Load node details
try:
    with open(node_details_path, 'r') as f:
        node_details = json.load(f)
        model_owner_cap_id = node_details.get("llama_owner_cap_id")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Error: Unable to load node details from {node_details_path}. Details: {e}")
    exit(1)

if not model_owner_cap_id:
    print("Error: Model owner capability ID is missing.")
    exit(1)

# Load SUI private key from keystore JSON
try:
    with open(keystore_path, 'r') as f:
        keys = json.load(f)
        if not keys:
            raise ValueError("Sui keystore file is empty. Please check your Sui configuration.")
        private_key = keys[0]  # Assuming the first key is used
except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
    print(f"Error: Unable to load SUI private key from {keystore_path}. Details: {e}")
    exit(1)

# Set environment variables
os.environ['PACKAGE_ID'] = package_id
os.environ['SUI_PRIVATE_KEY'] = private_key
os.environ['MODEL_OWNER_CAP_ID'] = model_owner_cap_id

# Command to run the Python script
command = [
    "python", "events/src/nexus_events/sui_event.py",
    "--packageid", package_id,
    "--privkey", private_key,
    "--modelownercapid", model_owner_cap_id,
    "--rpc", rpc_url,
    "--ws", ws_url,
    "--toolurl", tool_url  # New argument for tool URL
]

print(f"Running command: {' '.join(command)}")

# Execute the command
try:
    subprocess.run(command, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: Failed to execute command. Details: {e}")
    exit(1)
