# Use [run_trip_planner_example] to run the Trip Planner example.
# It's a blocking function that takes a client and package ID as arguments
# and then prompts the user for input to describe their trip details.

import textwrap
from colorama import Fore, Style
from nexus_sdk import (
    create_cluster,
    create_agent_for_cluster,
    create_task,
    execute_cluster,
    get_cluster_execution_response,
)


class TripPlanner:
    def __init__(
        self,
        client,
        package_id,
        model_id,
        model_owner_cap_id,
        origin,
        cities,
        date_range,
        interests,
    ):
        self.client = client
        self.package_id = package_id
        self.model_id = model_id
        self.model_owner_cap_id = model_owner_cap_id

        self.origin = origin
        self.cities = cities
        self.date_range = date_range
        self.interests = interests

    def setup_cluster(self):
        # Create a cluster (equivalent to Crew in CrewAI)
        cluster_id, cluster_owner_cap_id = create_cluster(
            self.client,
            self.package_id,
            "Trip Planning Cluster",
            "A cluster for planning the perfect trip",
        )
        return cluster_id, cluster_owner_cap_id

    def setup_agents(self, cluster_id, cluster_owner_cap_id):
        # Create agents (assuming we have model_ids and model_owner_cap_ids)
        agent_configs = [
            (
                "city_selector",
                "City Selection Expert",
                "Select the best city based on weather, season, and prices",
            ),
            (
                "local_expert",
                "Local Expert",
                "Provide the BEST insights about the selected city",
            ),
            (
                "travel_concierge",
                "Travel Concierge",
                "Create amazing travel itineraries with budget and packing suggestions",
            ),
        ]

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
                f"An AI agent specialized in {role.lower()} for trip planning.",
            )

    def setup_tasks(self, cluster_id, cluster_owner_cap_id):
        tasks = [
            (
                "identify_city",
                "city_selector",
                f"""
                Analyze and select the best city for the trip based on specific criteria.
                Consider weather patterns, seasonal events, and travel costs.
                Compare multiple cities, factoring in current weather conditions,
                upcoming events, and overall travel expenses.
                Provide a detailed report on the chosen city, including flight costs,
                weather forecast, and attractions.
                Origin: {self.origin}
                City Options: {self.cities}
                Trip Date: {self.date_range}
                Traveler Interests: {self.interests}
            """,
            ),
            (
                "gather_info",
                "local_expert",
                f"""
                As a local expert, compile an in-depth guide for the selected city.
                Include key attractions, local customs, special events, and daily activity recommendations.
                Highlight hidden gems and local favorites.
                Provide a comprehensive overview of the city's offerings, including cultural insights,
                must-visit landmarks, weather forecasts, and high-level costs.
                Trip Date: {self.date_range}
                Traveling from: {self.origin}
                Traveler Interests: {self.interests}
            """,
            ),
            (
                "plan_itinerary",
                "travel_concierge",
                f"""
                Create a full 7-day travel itinerary with detailed per-day plans.
                Include weather forecasts, places to eat, packing suggestions, and a budget breakdown.
                Suggest specific places to visit, hotels to stay at, and restaurants to try.
                Cover all aspects of the trip from arrival to departure.
                Format the plan as markdown, including a daily schedule, anticipated weather conditions,
                recommended clothing and items to pack, and a detailed budget.
                Explain why each place was chosen and what makes them special.
                Trip Date: {self.date_range}
                Traveling from: {self.origin}
                Traveler Interests: {self.interests}
            """,
            ),
        ]

        task_ids = []
        for task_name, agent_id, description in tasks:
            task_id = create_task(
                self.client,
                self.package_id,
                cluster_id,
                cluster_owner_cap_id,
                task_name,
                agent_id,
                description,
                f"Complete {task_name} for trip planning",
                description,
                "",  # No specific context provided in this example
            )
            task_ids.append(task_id)

        return task_ids

    def run(self):
        cluster_id, cluster_owner_cap_id = self.setup_cluster()
        self.setup_agents(cluster_id, cluster_owner_cap_id)
        self.setup_tasks(cluster_id, cluster_owner_cap_id)

        execution_id = execute_cluster(
            self.client,
            self.package_id,
            cluster_id,
            f"""
            Plan a trip from {self.origin} to one of these cities: {self.cities}.
            Travel dates: {self.date_range}
            Traveler interests: {self.interests}
        """,
        )

        if execution_id is None:
            return "Cluster execution failed"

        print(f"Cluster execution started with ID: {execution_id}")
        return get_cluster_execution_response(self.client, execution_id, 600)


# Runs the Trip Planner example using the provided Nexus package ID.
def run_trip_planner_example(client, package_id, model_id, mode_owner_cap):
    print(f"{Fore.CYAN}## Welcome to Trip Planner using Nexus{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}-------------------------------{Style.RESET_ALL}")

    origin = input(f"{Fore.GREEN}Where will you be traveling from? {Style.RESET_ALL}")
    cities = input(
        f"{Fore.GREEN}Which cities are you interested in visiting? {Style.RESET_ALL}"
    )
    date_range = input(
        f"{Fore.GREEN}What is your preferred date range for travel? {Style.RESET_ALL}"
    )
    interests = input(
        f"{Fore.GREEN}What are your main interests or hobbies? {Style.RESET_ALL}"
    )

    planner = TripPlanner(
        client,
        package_id,
        model_id,
        mode_owner_cap,
        origin,
        cities,
        date_range,
        interests,
    )

    print()
    result = planner.run()

    print(f"\n\n{Fore.CYAN}########################{Style.RESET_ALL}")
    print(f"{Fore.CYAN}## Here is your Trip Plan{Style.RESET_ALL}")
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
