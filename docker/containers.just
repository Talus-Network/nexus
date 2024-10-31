set shell := ["python3", "-c"]

[private]
default:
    @__import__('os').system("just -l containers")

[private]
[no-cd]
check:
    @import os, sys; from subprocess import call; result = call("docker ps | grep -q 'examples'", shell=True); \
    print("Docker environment is already running.") if result == 0 else (print("Docker environment is not running. Starting environment...") or os.system("just containers start"))

# Builds the Docker containers using Docker Compose
[no-cd]
build:
    @print("Building Docker containers..."); __import__('os').system("python3 ./docker/nexusctl.py create")

# Starts the Docker containers using Docker Compose
[no-cd]
start:
    @print("Starting Docker containers..."); __import__('os').system("python3 ./docker/nexusctl.py start")

# Stops the Docker containers using Docker Compose
[no-cd]
stop:
    @print("Stopping Docker containers..."); __import__('os').system("python3 ./docker/nexusctl.py stop")

# Deletes all Docker volumes related to the project using Docker Compose
[no-cd]
clean:
    @print("Deleting Docker volumes..."); __import__('os').system("python3 ./docker/nexusctl.py delete")
