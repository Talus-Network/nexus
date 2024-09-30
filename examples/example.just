# Examples assume that the dependencies are already installed in venv

[private]
default:
    @just -l example

# Runs an example that prompts the user for a description of their post.
[no-cd]
ig-post-planner:
    #!/usr/bin/env bash
    source .venv/bin/activate
    python3 examples/main.py "ig_post_planner"

# Runs an example that prompts the user for description of their trip.
[no-cd]
trip-planner:
    #!/usr/bin/env bash
    source .venv/bin/activate
    python3 examples/main.py "trip_planner"

# Runs an example that prompts the user for description of their cluster.
[no-cd]
cli-cluster:
    #!/usr/bin/env bash
    source .venv/bin/activate
    python3 examples/main.py "cli_cluster"
