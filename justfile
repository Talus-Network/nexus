# Variables for versioning and configurations
python_version := "3.10"
llama_version := "llama3.2:1b"

[private]
default:
    @just -l

# Commands for running examples
mod example 'examples/example.just'

# Build, Start, Stop or Clean Up docker containers 
mod containers 'docker/containers.just'

# Opens a Python shell inside the Docker container
interactive-shell:
    if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Opening an interactive Python shell in the Docker container..."; \
        docker exec -it examples /bin/bash -c "source .venv/bin/activate && ptpython"; \
    else \
        powershell -Command "docker exec -it examples /bin/bash -c 'source .venv/bin/activate && ptpython'"; \
    fi

# Builds and starts the entire environment
environment-up:
    if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Building and starting the entire environment..."; \
        python ./docker/nexusctl.py create; \
        python ./docker/nexusctl.py start; \
    else \
        powershell -Command "Write-Host 'Building and starting the entire environment...'; python ./docker/nexusctl.py create; python ./docker/nexusctl.py start"; \
    fi

# Shuts down and cleans up the environment
environment-down:
    if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Stopping and cleaning up the entire environment..."; \
        python ./docker/nexusctl.py stop; \
        python ./docker/nexusctl.py delete; \
    else \
        powershell -Command "Write-Host 'Stopping and cleaning up the entire environment...'; python ./docker/nexusctl.py stop; python ./docker/nexusctl.py delete"; \
    fi
