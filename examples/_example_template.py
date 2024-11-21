# Use [run_example] to run the example.
# It's a blocking function that takes a client and package ID as arguments
# and then prompts the user for input.

import textwrap
from colorama import Fore, Style
from nexus_sdk import (
    create_cluster,
    create_agent_for_cluster,
    create_task,
    execute_cluster,
    get_cluster_execution_response,
)

from _config_template import input_config, agent_configs, task_configs, init_prompt, cluster_config

class ClusterName:
    def __init__(
        self,
        client,
        package_id,
        model_id,
        model_owner_cap_id,
        # Dynamically set attributes based on provided inputs by the user
        **kwargs
    ):
        self.client = client
        self.package_id = package_id
        self.model_id = model_id
        self.model_owner_cap_id = model_owner_cap_id

        # Dynamically set attributes based on provided inputs
        for key, value in kwargs.items():
            setattr(self, key, value)       

    def setup_cluster(self):
        # Create a cluster (equivalent to Crew in CrewAI)
        cluster_id, cluster_owner_cap_id = create_cluster(
            self.client,
            self.package_id,
            # Add in the cluster name and description from the config file
            cluster_config["name"],
            cluster_config["description"],
        )
        return cluster_id, cluster_owner_cap_id

    def setup_agents(self, cluster_id, cluster_owner_cap_id):
        # Create agents (assuming we have model_ids and model_owner_cap_ids)
        # Agents are imported from the agent_configs list

        for agent_name, role, goal in agent_configs:
            create_agent_for_cluster(
                self.client,
                self.package_id,
                cluster_id,
                cluster_owner_cap_id,
                self.model_id,
                self.model_owner_cap_id,
                agent_name,
                role,
                goal,
                f"An AI agent specialized in {role.lower()}.",
            )

    def setup_tasks(self, cluster_id, cluster_owner_cap_id):
        # Create tasks for the agents
        # Tasks are imported from the task_configs list
        task_ids = []
        for task_name, agent_id, description in task_configs:
            task_id = create_task(
                self.client,
                self.package_id,
                cluster_id,
                cluster_owner_cap_id,
                task_name,
                agent_id,
                description,
                f"Complete {task_name} task",
                description,
                "",  # No specific context provided in this example
            )
            task_ids.append(task_id)

        return task_ids

    def run(self):
        cluster_id, cluster_owner_cap_id = self.setup_cluster()
        self.setup_agents(cluster_id, cluster_owner_cap_id)
        self.setup_tasks(cluster_id, cluster_owner_cap_id)
        
        # Execute the cluster, passing the initial prompt from the config file but formatting the string
        execution_id = execute_cluster(
            self.client,
            self.package_id,
            cluster_id,
            init_prompt.format(**self.__dict__),
        )

        if execution_id is None:
            return "Cluster execution failed"

        print(f"Cluster execution started with ID: {execution_id}")
        return get_cluster_execution_response(self.client, execution_id, 600)


# Runs the example using the provided Nexus package ID.
def run__example(client, package_id, model_id, mode_owner_cap):
    print(f"{Fore.CYAN}## Welcome to Nexus{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}-------------------------------{Style.RESET_ALL}")
    
    # Collect inputs in a dictionary
    user_inputs = {key: input(prompt) for key, prompt in input_config.items()}

    cluster = ClusterName(
        client,
        package_id,
        model_id,
        mode_owner_cap,
        **user_inputs
    )

    print()
    result = cluster.run()

    print(f"\n\n{Fore.CYAN}########################{Style.RESET_ALL}")
    print(f"{Fore.CYAN}## Here is your Solution{Style.RESET_ALL}")
    print(f"{Fore.CYAN}########################\n{Style.RESET_ALL}")

    paginate_output(result)


# Helper function to paginate the result output
def paginate_output(text, width=80):
    lines = text.split("\n")

    for i, line in enumerate(lines, 1):
        wrapped_line = textwrap.fill(line, width)
        print(wrapped_line)

        # It's nice when this equals the number of lines in the terminal, using
        # default value 32 for now.
        pause_every_n_lines = 32
        if i % pause_every_n_lines == 0:
            input(f"{Fore.YELLOW}-- Press Enter to continue --{Style.RESET_ALL}")
