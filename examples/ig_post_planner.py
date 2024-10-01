# Use [run_ig_post_planner_example] to run the Instagram Post Planner example.
# It's a blocking function that takes a client and package ID as arguments
# and then prompts the user for input to describe what product they want to market.

from nexus_sdk import (
    create_cluster,
    create_agent_for_cluster,
    create_task,
    execute_cluster,
    get_cluster_execution_response,
)


class InstagramPostPlanner:
    def __init__(
        self,
        client,
        package_id,
        model_id,
        model_owner_cap_id,
        product_website,
        product_details,
    ):
        self.client = client
        self.package_id = package_id
        self.model_id = model_id
        self.model_owner_cap_id = model_owner_cap_id

        self.product_website = product_website
        self.product_details = product_details

    def setup_cluster(self):
        cluster_id, cluster_owner_cap_id = create_cluster(
            self.client,
            self.package_id,
            "Instagram Post Planning Cluster",
            "A cluster for creating Instagram marketing content",
        )
        return cluster_id, cluster_owner_cap_id

    def setup_agents(self, cluster_id, cluster_owner_cap_id):
        agent_configs = [
            (
                "product_competitor",
                "Lead Market Analyst",
                "Conduct amazing analysis of products and competitors",
            ),
            (
                "strategy_planner",
                "Chief Marketing Strategist",
                "Synthesize insights to formulate incredible marketing strategies",
            ),
            (
                "creative_content",
                "Creative Content Creator",
                "Develop compelling content for social media campaigns",
            ),
            (
                "senior_photographer",
                "Senior Photographer",
                "Take amazing photographs for Instagram ads",
            ),
            (
                "chief_creative_director",
                "Chief Creative Director",
                "Oversee and approve the final content",
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
                f"An AI agent specialized in {role.lower()} for Instagram marketing.",
            )

    def setup_tasks(self, cluster_id, cluster_owner_cap_id):
        tasks = [
            (
                "product_analysis",
                "product_competitor",
                f"""
                Analyze the product website: {self.product_website}.
                Extra details: {self.product_details}.
                Identify unique features, benefits, and overall narrative.
                Report on key selling points, market appeal, and suggestions for enhancement.
            """,
            ),
            (
                "competitor_analysis",
                "product_competitor",
                f"""
                Explore competitors of: {self.product_website}.
                Identify top 3 competitors and analyze their strategies and positioning.
                Provide a detailed comparison to the competitors.
            """,
            ),
            (
                "campaign_development",
                "strategy_planner",
                f"""
                Create a targeted marketing campaign for: {self.product_website}.
                Develop a strategy and creative content ideas that will resonate with the audience.
                Include all context about the product and customer.
            """,
            ),
            (
                "instagram_ad_copy",
                "creative_content",
                """
                Craft 3 engaging Instagram post copy options.
                Make them punchy, captivating, and concise.
                Align with the product marketing strategy and highlight unique selling points.
                Encourage viewers to take action (visit website, make purchase, learn more).
            """,
            ),
            (
                "take_photograph",
                "senior_photographer",
                f"""
                Describe 3 amazing photo options for an Instagram post.
                Use the product details: {self.product_details}.
                Each description should be a paragraph, focusing on capturing audience attention.
                Don't show the actual product in the photo.
            """,
            ),
            (
                "review_photo",
                "chief_creative_director",
                f"""
                Review the 3 photo options from the senior photographer.
                Ensure they align with the product goals: {self.product_website}.
                Approve, ask clarifying questions, or suggest improvements.
                Provide 3 reviewed and improved photo descriptions.
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
                f"Complete {task_name} for Instagram post",
                description,
                "",
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
            Create an Instagram post for the product: {self.product_website}
            Additional details: {self.product_details}
            Provide both ad copy options and photo descriptions.
        """,
        )

        if execution_id is None:
            return "Cluster execution failed"

        print(f"Cluster execution started with ID: {execution_id}")
        return get_cluster_execution_response(self.client, execution_id, 600)


# Runs the Instagram Post Planner example using the provided Nexus package ID.
def run_ig_post_planner_example(client, package_id, model_id, mode_owner_cap):
    print("## Welcome to the Instagram Post Planner")
    print("-------------------------------")
    product_website = input(
        "What is the product website you want a marketing strategy for? "
    )
    product_details = input(
        "Any extra details about the product and/or the Instagram post you want? "
    )

    planner = InstagramPostPlanner(
        client, package_id, model_id, mode_owner_cap, product_website, product_details
    )
    result = planner.run()

    print("\n\n########################")
    print("## Here is the result")
    print("########################\n")
    print(result)
