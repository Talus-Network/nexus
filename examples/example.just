[private]
default:
    @just -l example

# Runs an example that prompts the user for a description of their post.
[no-cd]
ig-post-planner:
    @if [[ {{os()}} == "Linux" ]] || [[ {{os()}} == "macos" ]]; then \
        just containers check && \
        docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py ig_post_planner"; \
    else \
        powershell -Command "just containers check"; \
        powershell -Command "docker exec -it examples /bin/bash -c 'source .venv/bin/activate && python examples/main.py ig_post_planner'"; \
    fi

# Runs an example that prompts the user for description of their trip.
[no-cd]
trip-planner:
    if [[ {{os()}} == "Linux" ]] || [[ {{os()}} == "macos" ]]; then \
        just containers check && \
        docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py trip_planner"; \
    else \
        powershell -Command "just containers check"; \
        powershell -Command "docker exec -it examples /bin/bash -c 'source .venv/bin/activate && python examples/main.py trip_planner'"; \
    fi


# Runs an example that prompts the user for description of their cluster.
[no-cd]
cli-cluster:
    @if [[ {{os()}} == "Linux" ]] || [[ {{os()}} == "macos" ]]; then \
        just containers check && \
        docker exec -it examples /bin/bash -c "source .venv/bin/activate && python examples/main.py cli_cluster"; \
    else \
        powershell -Command "docker exec -it examples /bin/bash -c 'source .venv/bin/activate && python examples/main.py cli_cluster'"; \
    fi

check-os:
    @echo "{{os()}}"