# Runs an example that prompts the user to define a cluster, agents, tasks, and tools.

from nexus_sdk import (
    create_cluster,
    create_agent_for_cluster,
    create_task,
    execute_cluster,
    get_cluster_execution_response,
)
from pysui.sui.sui_txn.sync_transaction import SuiTransaction
from pysui.sui.sui_types.scalars import ObjectID, SuiString
from pysui.sui.sui_types.collections import SuiArray


def get_user_input_for_cluster():
    cluster_name = input("Enter Cluster name: ")
    cluster_description = input("Enter Cluster description: ")
    return cluster_name, cluster_description


def get_user_input_for_agent():
    agent_name = input("Enter Agent name: ")
    agent_role = input("Enter Agent role: ")
    agent_goal = input("Enter Agent goal: ")
    agent_backstory = input("Enter Agent backstory: ")
    return {
        "name": agent_name,
        "role": agent_role,
        "goal": agent_goal,
        "backstory": agent_backstory,
    }


def get_user_input_for_task():
    task_name = input("Enter Task name: ")
    agent_name = input("Enter Agent name for this task: ")
    task_description = input("Enter Task description: ")
    task_expected_output = input("Enter Task expected output: ")
    task_prompt = input("Enter Task prompt: ")
    task_context = input("Enter Task context: ")
    return {
        "name": task_name,
        "agent_name": agent_name,
        "description": task_description,
        "expected_output": task_expected_output,
        "prompt": task_prompt,
        "context": task_context,
    }


def get_user_input_for_tool():
    task_name = input("Enter Task name for this tool: ")
    tool_name = input("Enter Tool name: ")
    tool_args = input("Enter Tool args (separated by commas, no spaces): ")
    return {"task_name": task_name, "tool_name": tool_name, "tool_args": tool_args}


class CliCluster:
    def __init__(
        self,
        client,
        package_id,
        model_id,
        model_owner_cap_id,
        cluster_name,
        cluster_description,
        agents,
        tasks,
        tools,
    ):
        self.client = client
        self.package_id = package_id
        self.model_id = model_id
        self.model_owner_cap_id = model_owner_cap_id

        self.cluster_name = cluster_name
        self.cluster_description = cluster_description
        self.agents = agents
        self.tasks = tasks
        self.tools = tools

    def setup_cluster(self):
        cluster_id, cluster_owner_cap_id = create_cluster(
            self.client,
            self.package_id,
            self.cluster_name,
            self.cluster_description,
        )
        return cluster_id, cluster_owner_cap_id

    def setup_agents(self, cluster_id, cluster_owner_cap_id):
        for agent in self.agents:
            create_agent_for_cluster(
                self.client,
                self.package_id,
                cluster_id,
                cluster_owner_cap_id,
                self.model_id,
                self.model_owner_cap_id,
                agent["name"],
                agent["role"],
                agent["goal"],
                agent["backstory"],
            )

    def setup_tasks(self, cluster_id, cluster_owner_cap_id):
        for task in self.tasks:
            create_task(
                client=self.client,
                package_id=self.package_id,
                cluster_id=cluster_id,
                cluster_owner_cap_id=cluster_owner_cap_id,
                name=task["name"],
                agent_name=task["agent_name"],
                description=task["description"],
                expected_output=task["expected_output"],
                prompt=task["prompt"],
                context=task["context"],
            )

    def setup_tools(self, cluster_id, cluster_owner_cap_id):
        for tool in self.tools:
            self.attach_tool_to_task(
                cluster_id=cluster_id,
                cluster_owner_cap_id=cluster_owner_cap_id,
                task_name=tool["task_name"],
                tool_name=tool["tool_name"],
                tool_args=tool["tool_args"],
            )

    def attach_tool_to_task(
        self,
        cluster_id,
        cluster_owner_cap_id,
        task_name,
        tool_name,
        tool_args,
    ):
        txn = SuiTransaction(client=self.client)

        try:
            result = txn.move_call(
                target=f"{self.package_id}::cluster::attach_tool_to_task_entry",
                arguments=[
                    ObjectID(cluster_id),
                    ObjectID(cluster_owner_cap_id),
                    SuiString(task_name),
                    SuiString(tool_name),
                    SuiArray([SuiString(arg) for arg in tool_args]),
                ],
            )
        except Exception as e:
            print(f"Error in attach_task_to_tool: {e}")
            return None

        result = txn.execute(gas_budget=10000000)

        if result.is_ok():
            if result.result_data.effects.status.status == "success":
                print(f"Task attached to Tool")
                return True
            else:
                error_message = result.result_data.effects.status.error
                print(f"Transaction failed: {error_message}")
                return None
        return None

    def run(self, user_input):
        cluster_id, cluster_owner_cap_id = self.setup_cluster()
        self.setup_agents(cluster_id, cluster_owner_cap_id)
        self.setup_tasks(cluster_id, cluster_owner_cap_id)

        execution_id = execute_cluster(
            self.client,
            self.package_id,
            cluster_id,
            user_input,
        )

        if execution_id is None:
            return "Cluster execution failed"

        print(f"Cluster execution started with ID: {execution_id}")
        return get_cluster_execution_response(self.client, execution_id, 600)


# Runs the CLI agent example using the provided Nexus package ID.
def run_cli_cluster_example(client, package_id, model_id, mode_owner_cap):
    cluster_name, cluster_description = get_user_input_for_cluster()

    num_agents = int(input("How many agents would you like to define? "))
    num_tasks = int(input("How many tasks would you like to define? "))
    num_tools = int(input("How many tools would you like to define? "))

    agents = []
    for i in range(num_agents):
        print(f"\nEnter details for Agent {i+1}:")
        agent = get_user_input_for_agent()
        agents.append(agent)

    tasks = []
    for i in range(num_tasks):
        print(f"\nEnter details for Task {i+1}:")
        task = get_user_input_for_task()
        tasks.append(task)

    tools = []
    for i in range(num_tools):
        print(f"\nEnter details for Tool {i+1}:")
        tool = get_user_input_for_tool()
        tools.append(tool)

    cluster = CliCluster(
        client,
        package_id,
        model_id,
        mode_owner_cap,
        cluster_name,
        cluster_description,
        agents,
        tasks,
        tools,
    )

    print("Enter some text to start the execution with:")
    cluster.run(input())
