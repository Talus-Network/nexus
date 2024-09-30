from pysui.sui.sui_builders.get_builders import GetObject
from pysui.sui.sui_txn.sync_transaction import SuiTransaction
from pysui.sui.sui_types.scalars import ObjectID, SuiString
import time
import ast
import traceback

# Equal to 1 SUI which should be enough for most transactions.
GAS_BUDGET = 1000000000


# Creates an empty cluster object to which agents and tasks can be added.
# See functions [create_agent_for_cluster] and [create_task].
#
# Returns the cluster ID and the cluster owner capability ID.
def create_cluster(client, package_id, name, description, gas_budget=GAS_BUDGET):
    txn = SuiTransaction(client=client)

    try:
        result = txn.move_call(
            target=f"{package_id}::cluster::create",
            arguments=[SuiString(name), SuiString(description)],
        )
        result = txn.execute(gas_budget=gas_budget)
        if result.is_ok():
            if result.result_data.effects.status.status == "success":
                # just because it says "parsed_json" doesn't mean it's actually valid JSON apparently
                not_json = result.result_data.events[0].parsed_json
                created_event = ast.literal_eval(not_json.replace("\n", "\\n"))
                cluster_id = created_event["cluster"]
                cluster_owner_cap_id = created_event["owner_cap"]

                return cluster_id, cluster_owner_cap_id
        print(f"Failed to create Cluster: {result.result_string}")
        return None
    except Exception as e:
        print(f"Error in create_cluster: {e}")
        return None


# Creates a new agent for the given cluster.
# This means that the agent does not live on-chain as a standalone object that
# other clusters could reference.
def create_agent_for_cluster(
    client,
    package_id,
    cluster_id,
    cluster_owner_cap_id,
    model_id,
    model_owner_cap_id,
    name,
    role,
    goal,
    backstory,
    gas_budget=GAS_BUDGET,
):
    txn = SuiTransaction(client=client)

    try:
        result = txn.move_call(
            target=f"{package_id}::cluster::add_agent_entry",
            arguments=[
                ObjectID(cluster_id),
                ObjectID(cluster_owner_cap_id),
                ObjectID(model_id),
                ObjectID(model_owner_cap_id),
                SuiString(name),
                SuiString(role),
                SuiString(goal),
                SuiString(backstory),
            ],
        )
        result = txn.execute(gas_budget=gas_budget)
        if result.is_ok():
            return True
        print(f"Failed to add Agent: {result.result_string}")
        return False
    except Exception as e:
        print(f"Error in create_agent: {e}")
        return False


# Creates a new task for the given cluster.
# Each task must be executed by an agent that is part of the cluster.
def create_task(
    client,
    package_id,
    cluster_id,
    cluster_owner_cap_id,
    name,
    agent_name,
    description,
    expected_output,
    prompt,
    context,
    gas_budget=GAS_BUDGET,
):
    txn = SuiTransaction(client=client)

    try:
        result = txn.move_call(
            target=f"{package_id}::cluster::add_task_entry",
            arguments=[
                ObjectID(cluster_id),
                ObjectID(cluster_owner_cap_id),
                SuiString(name),
                SuiString(agent_name),
                SuiString(description),
                SuiString(expected_output),
                SuiString(prompt),
                SuiString(context),
            ],
        )
        result = txn.execute(gas_budget=gas_budget)
        if result.is_ok():
            return True
        print(f"Failed to add Task: {result.result_string}")
        return False
    except Exception as e:
        print(f"Error in create_task: {e}")
        return False


# Begins execution of a cluster.
# Returns the cluster execution ID.
# Use the function [get_cluster_execution_response] to fetch the response of the execution
# in a blocking manner.
def execute_cluster(
    client,
    package_id,
    cluster_id,
    input,
    gas_budget=GAS_BUDGET,
):
    txn = SuiTransaction(client=client)

    try:
        result = txn.move_call(
            target=f"{package_id}::cluster::execute",
            arguments=[ObjectID(cluster_id), SuiString(input)],
        )
    except Exception as e:
        print(f"Error in execute_cluster: {e}")
        traceback.print_exc()
        return None

    result = txn.execute(gas_budget=gas_budget)

    if result.is_ok():
        if result.result_data.effects.status.status == "success":
            # just because it says "parsed_json" doesn't mean it's actually valid JSON apparently
            not_json = result.result_data.events[0].parsed_json
            created_event = ast.literal_eval(not_json.replace("\n", "\\n"))

            # There's going to be either field "execution" or "cluster execution"
            # because there are two events emitted in the tx.
            # We could check for the event name or just try both.
            execution_id = created_event.get(
                "execution", created_event.get("cluster_execution")
            )

            return execution_id
        else:
            error_message = result.result_data.effects.status.error
            print(f"Execute Cluster Transaction failed: {error_message}")
            return None
    else:
        print(f"Failed to create ClusterExecution: {result.result_string}")
        return None


# Fetches the response of a cluster execution.
# If the execution is not complete within the specified time, the function returns a timeout message.
def get_cluster_execution_response(
    client, execution_id, max_wait_time_s=180, check_interval_s=5
):
    start_time = time.time()
    while time.time() - start_time < max_wait_time_s:
        try:
            # Create a GetObject builder
            get_object_builder = GetObject(object_id=ObjectID(execution_id))

            # Execute the query
            result = client.execute(get_object_builder)

            if result.is_ok():
                object_data = result.result_data
                if object_data and object_data.content:
                    fields = object_data.content.fields
                    status = fields.get("status")
                    if status == "SUCCESS":
                        return fields.get("cluster_response")
                    elif status == "FAILED":
                        return f"Execution failed: {fields.get('error_message')}"
                    elif status == "IDLE":
                        print("Execution has not started yet.")
                    elif status == "RUNNING":
                        until_timeout = max_wait_time_s - (time.time() - start_time)
                        print(
                            "Execution is still running, waiting... (%.2fs until timeout)"
                            % until_timeout
                        )
                    else:
                        return f"Unknown status: {status}"

                time.sleep(check_interval_s)
            else:
                return f"Failed to get object: {result.result_string}"

        except Exception as e:
            return f"Error checking execution status: {e}"

    return "Timeout: Execution did not complete within the specified time."
