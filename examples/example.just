# Examples assume that the dependencies are already installed in venv

[private]
default:
    @just -l example

# Runs an example that prompts the user for a description of their post.
[no-cd]
ig-post-planner:
    docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py ig_post_planner"

# Runs an example that prompts the user for description of their trip.
[no-cd]
trip-planner:
    docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py trip_planner"

# Runs an example that prompts the user for description of their cluster.
[no-cd]
cli-cluster:
    docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py cli_cluster"

