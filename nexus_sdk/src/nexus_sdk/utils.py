from pysui.sui.sui_clients.sync_client import SuiClient
from pysui.sui.sui_config import SuiConfig


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
