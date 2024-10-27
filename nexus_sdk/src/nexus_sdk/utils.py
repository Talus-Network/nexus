import json
from pathlib import Path
from pysui import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.abstracts.client_keypair import SignatureScheme


# Returns Sui client with the given private key.
def get_sui_client(
    private_key,
    rpc_url="http://localhost:9000",
    ws_url="ws://localhost:9000",
):
    return SuiClient(
        SuiConfig.user_config(
            rpc_url=rpc_url,
            ws_url=ws_url,
            prv_keys=[private_key],
        )
    )


# Utility function to create a Sui client with airdrop (faucet)
def get_sui_client_with_airdrop(
    rpc_url="http://localhost:9000",
    ws_url="ws://localhost:9000",
    faucet_url="http://localhost:5003/gas",
    keystore_path=Path("./sui.keystore"),
):

    if not keystore_path.exists():
        keystore_path.parent.mkdir(parents=True, exist_ok=True)
        keystore_path.touch()
        sui_config = SuiConfig.user_config(rpc_url=rpc_url, ws_url=ws_url)

        _, address = sui_config.create_new_keypair_and_address(
            scheme=SignatureScheme.ED25519
        )

        sui_config._faucet_url = faucet_url

        client = SuiClient(sui_config)

        result = client.get_gas_from_faucet()
        if not result:
            raise Exception("Failed to get gas from faucet")

        sui_config._write_keypairs(keystore_path)
        print(f"New wallet created and funded. Address: {address}")
        return client
    else:
        with open(keystore_path, "r") as f:
            keys = json.load(f)
            if not keys:
                raise ValueError(
                    "Sui keystore file is empty. Please check your Sui configuration."
                )
            private_key = keys[0]  # Assuming the first key is used
        return get_sui_client(private_key, rpc_url=rpc_url, ws_url=ws_url)
