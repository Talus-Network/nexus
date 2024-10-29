[private]
default:
    @just -l containers

[private]
[no-cd]
check:
    # If the system is Linux or macOS, execute the check with bash.
    @if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        if ! docker ps | grep -q "examples"; then \
            echo "Docker environment is not running. Starting environment..."; \
            just containers start; \
        else \
            echo "Docker environment is already running."; \
        fi; \
    else \
        powershell -Command "if (!(docker ps | Select-String -Quiet 'examples')) { Write-Host 'Docker environment is not running. Starting environment...'; just containers start } else { Write-Host 'Docker environment is already running.' }"; \
    fi

# Builds the Docker containers using Docker Compose
[no-cd]
build:
    @if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Building Docker containers..."; \
        python ./docker/nexusctl.py create; \
    else \
        powershell -Command "Write-Host 'Building Docker containers...'; python ./docker/nexusctl.py create"; \
    fi

# Starts the Docker containers using Docker Compose
[no-cd]
start:
    @if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Starting Docker containers..."; \
        python ./docker/nexusctl.py start; \
    else \
        powershell -Command "Write-Host 'Starting Docker containers...'; python ./docker/nexusctl.py start"; \
    fi

# Stops the Docker containers using Docker Compose
[no-cd]
stop:
    @if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Stopping Docker containers..."; \
        python ./docker/nexusctl.py stop; \
    else \
        powershell -Command "Write-Host 'Stopping Docker containers...'; python ./docker/nexusctl.py stop"; \
    fi

# Deletes all Docker volumes related to the project using Docker Compose
[no-cd]
clean:
    @if [[ {{os()}} == "linux" ]] || [[ {{os()}} == "macos" ]]; then \
        echo "Deleting Docker volumes..."; \
        python ./docker/nexusctl.py delete; \
    else \
        powershell -Command "Write-Host 'Deleting Docker volumes...'; python ./docker/nexusctl.py delete"; \
    fi
