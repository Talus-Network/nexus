set shell := [ "python3", "-c"]

[private]
default: version-check
   @__import__('os').system("just -l example")

[private]
version-check:
    @import sys; major, minor = sys.version_info[:2]; \
    assert (major, minor) >= (3, 7), "This script requires at least Python 3.7. Please link \"python3\" to Python 3.7 or higher and try again."
    

# Runs an example that prompts the user for a description of their post.
[no-cd]
ig-post-planner:
    @__import__('os').system("just containers check")
    @__import__('os').system("docker exec -it examples /bin/bash -c \"source .venv/bin/activate && python examples/main.py ig_post_planner\"")

# Runs an example that prompts the user for description of their trip.
[no-cd]
trip-planner:
    @__import__('os').system("just containers check")
    @__import__('os').system("docker exec -it examples /bin/bash -c \"source .venv/bin/activate && python examples/main.py trip_planner\"")

# Runs an example that prompts the user for description of their cluster.
[no-cd]
cli-cluster:
    @__import__('os').system("just containers check")
    @__import__('os').system("docker exec -it examples /bin/bash -c \"source .venv/bin/activate && python examples/main.py cli_cluster\"")
