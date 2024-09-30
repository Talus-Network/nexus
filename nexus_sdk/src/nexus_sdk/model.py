from pysui.sui.sui_txn.sync_transaction import SuiTransaction
from pysui.sui.sui_types.scalars import ObjectID, SuiU64, SuiU8, SuiString, SuiBoolean
from pysui.sui.sui_types.collections import SuiArray
import ast


# Creates a new on-chain model object.
# Returns the model ID and the model owner capability ID.
def create_model(
    client,
    package_id,
    node_id,
    name,
    model_hash,
    url,
    token_price,
    capacity,
    num_params,
    description,
    max_context_length,
    is_fine_tuned,
    family,
    vendor,
    is_open_source,
    datasets,
):
    txn = SuiTransaction(client=client)

    args = [
        ObjectID(node_id),
        SuiString(name),
        SuiArray([SuiU8(b) for b in model_hash]),
        SuiString(url),
        SuiU64(token_price),
        SuiU64(capacity),
        SuiU64(num_params),
        SuiString(description),
        SuiU64(max_context_length),
        SuiBoolean(is_fine_tuned),
        SuiString(family),
        SuiString(vendor),
        SuiBoolean(is_open_source),
        SuiArray([SuiString(dataset) for dataset in datasets]),
    ]

    result = txn.move_call(
        target=f"{package_id}::model::create",
        arguments=args,
    )
    result = txn.execute(gas_budget=10000000)

    if result.is_ok():
        effects = result.result_data.effects
        if effects.status.status == "success":
            # just because it says "parsed_json" doesn't mean it's actually valid JSON apparently
            not_json = result.result_data.events[0].parsed_json
            created_event = ast.literal_eval(not_json.replace("\n", "\\n"))

            model_id = created_event["model"]
            model_owner_cap_id = created_event["owner_cap"]
            return model_id, model_owner_cap_id

    return None
