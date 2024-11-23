#Imports
from nexus_sdk import (
    create_cluster,
    create_agent_for_cluster,
    create_task,
    execute_cluster,
    get_cluster_execution_response,
)

class EventPlanner:
    #constructor
    def __init__(
        self,
        client,
        package_id,
        model_id,
        model_owner_cap_id,
        event_details,
        total_budget,
        time_frame,

    ):  #assign variables
        self.client = client
        self.package_id = package_id
        self.model_id = model_id
        self.model_owner_cap_id = model_owner_cap_id

        #user input variables
        self.event_details = event_details
        self.total_budget = total_budget
        self.time_frame = time_frame

    #function to create cluster
    def setup_cluster(self):
        cluster_id, cluster_owner_cap_id = create_cluster(
            self.client,
            self.package_id,
            "Event Planning Cluster", #cluster name
            "A cluster for planning events", #cluster description
        )
        return cluster_id, cluster_owner_cap_id

    def setup_agents(self, cluster_id, cluster_owner_cap_id):
        #Define each agent in the order of agent_name, role, goal
        agent_configs = [
            (
                "Event_Details_Gatherer",
                "Details Gatherer",
                "Brainstorm necessary details for planning the event '{self.event_details}', including theme, guest count, and preferences.",
            ),
            (
                "Budget_Allocator",
                "Budget Planner",
                "Allocate the total budget of ${self.total_budget} for different aspects of the event, such as food, decor, and entertainment using details from {self.event_details}.",
            ),
            (
                "Schedule_Organizer",
                "Scheduler",
                "Create a detailed schedule for the event '{self.event_details}' within the time frame: {self.time_frame}.",
            ),
            (
                "Message_Creator",
                "Message Creator",
                "Please draft an invitation message for guests using the details provided in {self.event_details}.",
            ),
        ]

        #loop through agent_configs array and create each agent
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
                f"An AI agent specialized in {role.lower()} for event planning.",
            )

    def setup_tasks(self, cluster_id, cluster_owner_cap_id):
        #Define each task in the order of task_name, agent_id, description
        #Note that the agent_id should be the same as the agent_name in setup_agents
        tasks = [
            (
                "gather_event_details",
                "Event_Details_Gatherer",
                f"""
                Brainstorm and collect key details for the event '{self.event_details}'. 
                Focus on:
                    - The event's theme (e.g., elegant, casual, futuristic)
                    - Number of guests
                    - Any special preferences or requests (e.g., dietary restrictions, activities)
                Provide these details in a structured format for further planning.
                """,
            ),
            (
                "allocate_budget",
                "Budget_Allocator",
                f"""
                Based on the details collected about the event '{self.event_details}', allocate the total budget of ${self.total_budget} 
                across the following categories:
                    - Food and catering
                    - Decorations
                    - Entertainment
                    - Miscellaneous (e.g., venue costs)
                Ensure that the budget allocation matches the event's priorities and any constraints provided.
                Provide a breakdown of the budget for each category in a clear format.
                """,
            ),
            (
                "organize_schedule",
                "Schedule_Organizer",
                f"""
                Create a detailed schedule for the event '{self.event_details}' within the time frame: {self.time_frame}. 
                The schedule should include:
                    - Key activities (e.g., speeches, meals, entertainment)
                    - Start and end times for each activity
                    - Breaks or transition times (if needed)
                Ensure the schedule is realistic and leaves room for flexibility. Provide the schedule in an easy-to-read format.
                """,
            ),
             (
                "create_message",
                "Message_Creator",
                f"""
                Draft a clear and engaging invitation message for the event '{self.event_details}'.
                The message should include:
                    - The event name and purpose.
                    - The date, time, and location of the event.
                    - Any specific details or instructions for the guests (e.g., dress code, RSVP information).
                    - Ensure the message is welcoming, concise, and provides all necessary details for the recipient to understand and attend the event.
                """,
            ),
        ]

        #loop through tasks array and create each task
        task_ids = []
        for task_name, agent_id, description in tasks:
            task_id = create_task( #Nexus SDK function call
                self.client,
                self.package_id,
                cluster_id,
                cluster_owner_cap_id,
                task_name,
                agent_id,
                description,
                description,   #expected output parameter
                f"Complete {task_name} for planning events", #prompt parameter
                "be thorough and detailed", #context parameter
            )
            task_ids.append(task_id)

        return task_ids
    
    #function to run the cluster
    def run(self):
        cluster_id, cluster_owner_cap_id = self.setup_cluster()
        self.setup_agents(cluster_id, cluster_owner_cap_id)
        self.setup_tasks(cluster_id, cluster_owner_cap_id)

        execution_id = execute_cluster(
            self.client,
            self.package_id,
            cluster_id,
            #input parameter
            f""" 
            Plan the event: {self.event_details} with the following information:
                - Total budget: ${self.total_budget}
                - Time frame: {self.time_frame}
            Tasks to accomplish:
                1. Gather necessary details about the event, including theme, guest count, and preferences.
                2. Allocate the total budget across key categories like food, decorations, and entertainment.
                3. Create a detailed schedule for the event within the given time frame.

            Ensure the plan is detailed and formatted in a way that is easy to review and execute.
        """,
        )

        if execution_id is None:
            return "Cluster execution failed"

        print(f"Cluster execution started with ID: {execution_id}")
        return get_cluster_execution_response(self.client, execution_id, 600)


# Runs the Event Planner Example using the provided Nexus package ID.
def run_event_planner_example(client, package_id, model_id, mode_owner_cap):
    print("## Welcome to the Event Planning Example")
    print("-------------------------------")
    
    event_details = input("Enter the event details (e.g., type, purpose, theme, and guest count): ")
    total_budget = float(input("Enter the total budget for the event (in dollars): "))
    time_frame = input("Enter the time frame for the event (e.g., 3 hours, 1 day) as well as the start time: ")
    summarizer = EventPlanner(client, package_id, model_id, mode_owner_cap,event_details, total_budget, time_frame)
    result = summarizer.run()

    print("\n\n########################")
    print("## Here is the result")
    print("########################\n")
    print(result)

    
