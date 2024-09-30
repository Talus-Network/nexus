from pysui.sui.sui_txn.sync_transaction import SuiTransaction
from pysui.sui.sui_types.scalars import SuiU64


# Creates a new node owned object.
# Returns the node ID.
def create_node(client, package_id, name, node_type, gpu_memory):
    txn = SuiTransaction(client=client)

    result = txn.move_call(
        target=f"{package_id}::node::create",
        arguments=[name, node_type, SuiU64(gpu_memory), "c", []],
    )
    result = txn.execute(gas_budget=10000000)

    if result.is_ok() or result._data.succeeded:
        node_id = result._data.effects.created[0].reference.object_id
        return node_id
    else:
        print(f"Failed to create node: {result.result_string}")
        return None
