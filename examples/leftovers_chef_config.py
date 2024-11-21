from colorama import Fore, Style

# User input: name of the arguments and the prompt to ask the user
# Example input: "name": "What is your name?",
input_config = {
    "leftover_ingredients": f"{Fore.GREEN}What ingredients do you have left over? {Style.RESET_ALL}",
    "budget": f"{Fore.YELLOW}What is the budget you want to spend for additional ingredients? {Style.RESET_ALL}",
    "effort_level" : f"{Fore.YELLOW}What level of effort do you want to spend perparing the meal? {Style.RESET_ALL}",
    "preferences": f"{Fore.RED}Do you have any preferences or dietarty restrictions? {Style.RESET_ALL}",
}

# Initial prompt
# Refer to the the variables you've defined like so, "{variable_name}""
init_prompt = """
    Suggest a list of 5 meals based on these leftover ingredients: {leftover_ingredients}.
    Consider the following:
    - Budget (for purchasing the remaining ingredients, if any): {budget}
    - Effort Level: {effort_level}
    - Preferences (type of cuisine, dietary restrictions, allergies): {preferences}
    Give a sustainability score for each meal and highlight the most sustainable options.
"""

# Setting up the cluster
cluster_config = {
    "name": "Leftovers Chef Cluster",
    "description": "A cluster for making a meal out of leftovers",
}

# Agent(s) Configuration
agent_configs = [
    (
        "meal_designer",
        "Meal Design Expert",
        "Will design meals based on the leftover ingredients in your fridge",
    ),
    (
        "chef",
        "Chef",
        "Provides the full list of ingredients needed and the instructions to prepare the meal",
    ),
]

# Task(s) Configuration
# Refer to the the variables you've defined like so, "{variable_name}"".
# String will be formatted in the main program. Leave it as regular string here.
task_configs = [
    (
        "design_menu",
        "meal_designer",
        """
        Design a meal that includes, but is not limited to, the leftover ingredients ({leftover_ingredients}) provided as inputs.
        Consider the budget, {budget}, effort level, {effort_level}, and preferences, {preferences} of the user.
        Suggest in total 5 dishes that are compatible with the inputs.
    """,
    ),

    (
        "prepare_meal",
        "chef",
        """
        Provide a detailed recipe for preparing each of the proposed meals provided by the menu designer.
        Include a list of all ingredients required, step-by-step instructions, and estimated cooking time.
        Specify the cooking equipment needed and the difficulty level ({effort_level}) of the recipe.
    """,
    ),
]
