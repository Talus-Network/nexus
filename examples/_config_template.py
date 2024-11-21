from colorama import Fore, Style

# User input: name of the arguments and the prompt to ask the user for input
# Example input: "name": "What is your name?",
input_config = {
    "arg_name": f"{Fore.YELLOW}Put a prompt here for arg_name... {Style.RESET_ALL}",
    "another_arg_name": f"{Fore.YELLOW}Put another prompt here for another_arg_name... {Style.RESET_ALL}",
}

# Initial prompt
# Refer to the the variables you've defined like so, "{variable_name}"".
# String will be formatted in the main program. Leave it as regular string here.
init_prompt = "Put the initial prompt to run the cluster execution here."

# Setting up the cluster
cluster_config = {
    "name": "Put Cluster Name here",
    "description": "Put Cluster Description here",
}

# Agent(s) Configuration
agent_configs = [
    (
        "name",
        "role",
        "goal",
        "backstory",
    ),
]

# Task(s) Configuration
# Refer to the the variables you've defined like so, "{variable_name}"".
# String will be formatted in the main program. Leave it as regular string here.
task_configs = [
    (
        "Put the Task name here",
        "Put the Agent name (performing the task) here",
        """"
        Put the task description here.
    """,
    ),
]
