import os
import platform
import subprocess
import sys
import re
import argparse
import time
import signal

# Set OLLAMA_PID_FILE to a path in the /tmp directory
OLLAMA_PID_FILE = "/tmp/ollama.pid"


def load_env_file(env_path):
    """Loads environment variables from a .env file and adds them to os.environ."""
    try:
        with open(env_path, "r") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key, value = key.strip(), value.strip()
                    os.environ[key] = value
    except FileNotFoundError:
        print(f"Environment file {env_path} not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading environment file: {e}")
        sys.exit(1)


def get_docker_compose_version():
    try:
        result = subprocess.run(
            ["docker", "compose", "version"], capture_output=True, text=True, check=True
        )
        version_line = result.stdout.strip()
        return version_line
    except subprocess.CalledProcessError:
        print(
            "Error checking Docker Compose version. Make sure Docker Compose is installed."
        )
        sys.exit(1)


def extract_major_minor(version_line):
    try:
        match = re.search(r"v?(\d+)\.(\d+)", version_line)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2))
            return major, minor
        else:
            print("Could not parse Docker Compose version string.")
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while extracting version: {e}")
        sys.exit(1)


def check_docker_compose_version():
    version_line = get_docker_compose_version()
    if version_line:
        print(f"Docker Compose version line: {version_line}")
        major, minor = extract_major_minor(version_line)
        if major < 2 or (major == 2 and minor < 20):
            print(
                f"Docker Compose version {major}.{minor} is too old. Please update to version 2.20 or higher."
            )
            sys.exit(1)
        else:
            print(f"Docker Compose version {major}.{minor} is sufficient.")


def check_brew_installed():
    try:
        subprocess.run(
            ["brew", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        print("Brew is installed.")
    except subprocess.CalledProcessError:
        print(
            "Brew is not installed. Please install Homebrew from https://brew.sh/ and try again."
        )
        sys.exit(1)
    except FileNotFoundError:
        print(
            "Brew is not installed. Please install Homebrew from https://brew.sh/ and try again."
        )
        sys.exit(1)


def detect_gpu_and_set_env():
    os_type = platform.system()
    if os_type == "Windows":
        print("Running on Windows")
        if (
            subprocess.run(
                ["where", "nvidia-smi"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            print("NVIDIA GPU detected")
            os.environ["OLLAMA_DEVICE_DRIVER"] = "nvidia"
            os.environ["OLLAMA_DEVICE_COUNT"] = "all"
            os.environ["OLLAMA_DEVICE_CAPABILITIES"] = "gpu"
        else:
            print("No GPU detected")
            os.environ["OLLAMA_DEVICE_DRIVER"] = ""
            os.environ["OLLAMA_DEVICE_COUNT"] = ""
            os.environ["OLLAMA_DEVICE_CAPABILITIES"] = ""
    elif os_type == "Linux":
        print("Running on Linux")
        if (
            subprocess.run(
                ["which", "nvidia-smi"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        ):
            print("NVIDIA GPU detected")
            os.environ["OLLAMA_DEVICE_DRIVER"] = "nvidia"
            os.environ["OLLAMA_DEVICE_COUNT"] = "all"
            os.environ["OLLAMA_DEVICE_CAPABILITIES"] = "gpu"
        else:
            print("No GPU detected")
            os.environ["OLLAMA_DEVICE_DRIVER"] = ""
            os.environ["OLLAMA_DEVICE_COUNT"] = ""
            os.environ["OLLAMA_DEVICE_CAPABILITIES"] = ""
    elif os_type == "Darwin":
        print("Running on macOS")
        os.environ["OLLAMA_DEVICE_DRIVER"] = ""
        os.environ["OLLAMA_DEVICE_COUNT"] = ""
        os.environ["OLLAMA_DEVICE_CAPABILITIES"] = ""
    else:
        print(f"Unsupported OS: {os_type}")
        sys.exit(1)


def start_ollama_serve():
    os_type = platform.system()
    if os_type == "Darwin":
        # Check if brew is installed
        check_brew_installed()

        # Check if ollama is installed with brew
        try:
            if (
                subprocess.run(
                    ["brew", "list", "ollama"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode
                != 0
            ):
                print("Ollama not found, installing using brew...")
                subprocess.run(["brew", "install", "ollama"], check=True)
            else:
                print("Ollama is already installed.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install ollama: {e}")
            sys.exit(1)

        # Start the ollama serve process and pull the model
        try:
            model_version = os.getenv("LLAMA_MODEL_VERSION")
            if not model_version:
                print("LLAMA_MODEL_VERSION environment variable is not set.")
                sys.exit(1)

            # Start ollama serve in the background
            print("Starting Ollama server...")
            serve_command = "nohup ollama serve &"
            subprocess.Popen(
                serve_command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Wait for the server to start and capture the correct PID
            print("Waiting for Ollama to start...")
            time.sleep(5)  # Give it some time to properly start

            # Find the process PID using pgrep
            result = subprocess.run(
                ["pgrep", "-f", "ollama serve"], capture_output=True, text=True
            )
            if result.stdout:
                pid = int(result.stdout.strip())
                print(f"Ollama server started with PID: {pid}")

                # Save the PID to a file
                with open(OLLAMA_PID_FILE, "w") as pid_file:
                    pid_file.write(str(pid))
                print(f"Saved Ollama PID to {OLLAMA_PID_FILE}")
            else:
                print("Failed to find the Ollama serve process.")
                sys.exit(1)

            # Pull the specified model
            print(f"Pulling model version: {model_version}")
            subprocess.run(["ollama", "pull", model_version], check=True)

        except subprocess.CalledProcessError as e:
            print(f"Error while starting Ollama or pulling model: {e}")
            sys.exit(1)


def change_to_docker_directory():
    try:
        os.chdir("./docker")
        print(f"Changed working directory to: {os.getcwd()}")
    except FileNotFoundError:
        print(
            "Directory './docker' does not exist. Please make sure the directory is correct."
        )
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error while changing directory: {e}")
        sys.exit(1)


def docker_compose_up():
    change_to_docker_directory()
    os_type = platform.system()

    compose_file = "docker-compose.yaml"
    if os_type == "Darwin":
        # Use a different compose file for macOS
        compose_file = "docker-compose-nollama.yaml"
        print("Using docker-compose-nollama.yaml for macOS")

        # Override the MODEL_URL environment variable on macOS
        os.environ["MODEL_URL"] = "http://host.docker.internal:11434"

    # Load environment variables from the .env file
    load_env_file(".env")

    # Ensure the environment has the updated MODEL_URL for macOS
    env_vars = os.environ.copy()
    if os_type == "Darwin":
        env_vars["MODEL_URL"] = "http://host.docker.internal:11434"

    try:
        # Use subprocess.run with env argument to override environment variables
        subprocess.run(
            ["docker", "compose", "-f", compose_file, "up", "-d"],
            check=True,
            env=env_vars,  # Pass our modified environment with correct MODEL_URL
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Docker Compose up: {e}")
        sys.exit(1)


def docker_compose_build():
    change_to_docker_directory()
    os_type = platform.system()

    compose_file = "docker-compose.yaml"
    if os_type == "Darwin":
        # Use a different compose file for macOS
        compose_file = "docker-compose-nollama.yaml"
        print("Using docker-compose-nollama.yaml for macOS")

        # Override the MODEL_URL environment variable on macOS
        os.environ["MODEL_URL"] = "http://host.docker.internal:11434"

    # Load environment variables from the .env file
    load_env_file(".env")

    # Ensure the environment has the updated MODEL_URL for macOS
    env_vars = os.environ.copy()
    if os_type == "Darwin":
        env_vars["MODEL_URL"] = "http://host.docker.internal:11434"

    try:
        # Use subprocess.run with env argument to override environment variables
        subprocess.run(
            ["docker", "compose", "-f", compose_file, "build"],
            check=True,
            env=env_vars,  # Pass our modified environment with correct MODEL_URL
        )
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Docker Compose build: {e}")
        sys.exit(1)


def docker_compose_down():
    change_to_docker_directory()
    os_type = platform.system()

    compose_file = "docker-compose.yaml"
    if os_type == "Darwin":
        # Use a different compose file for macOS
        compose_file = "docker-compose-nollama.yaml"
        print("Using docker-compose-nollama.yaml for macOS")

    try:
        subprocess.run(["docker", "compose", "-f", compose_file, "down"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to run Docker Compose down: {e}")
        sys.exit(1)

    # If running on macOS, stop the Ollama serve process
    if os_type == "Darwin":
        stop_ollama_serve()


def docker_delete_volumes():
    try:
        # List of volumes to delete
        volumes_to_delete = [
            "docker_fullnode1-db",
            "docker_genesis",
            "docker_shared",
            "docker_validator1-db",
            "docker_validator2-db",
            "docker_validator3-db",
            "docker_validator4-db",
        ]
        for volume in volumes_to_delete:
            subprocess.run(["docker", "volume", "rm", volume], check=True)
        print("All specified Docker volumes deleted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to delete Docker volumes: {e}")
        sys.exit(1)


def stop_ollama_serve():
    """Stops the Ollama server and all related processes if they are running."""
    if os.path.exists(OLLAMA_PID_FILE):
        try:
            with open(OLLAMA_PID_FILE, "r") as pid_file:
                pid = int(pid_file.read().strip())
                print(f"Stopping Ollama server with PID: {pid}")
                os.kill(pid, signal.SIGTERM)  # Send SIGTERM to the main ollama process

            # Remove the PID file
            os.remove(OLLAMA_PID_FILE)
            print(f"PID file {OLLAMA_PID_FILE} deleted.")

            # Find and kill any remaining related processes (e.g., ollama_llama_server)
            related_processes = subprocess.run(
                ["pgrep", "-f", "ollama"], capture_output=True, text=True
            )
            if related_processes.stdout:
                pids = related_processes.stdout.strip().split("\n")
                for related_pid in pids:
                    print(f"Killing related Ollama process with PID: {related_pid}")
                    os.kill(
                        int(related_pid), signal.SIGTERM
                    )  # Use SIGTERM to allow graceful shutdown
        except ProcessLookupError:
            print(
                f"Error stopping Ollama server: No such process with PID {pid}. It may have already been stopped."
            )
        except Exception as e:
            print(f"Error stopping Ollama server: {e}")
    else:
        print(
            f"PID file {OLLAMA_PID_FILE} not found. Ollama server may not be running."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Control the Docker Compose deployment and overall environment."
    )
    parser.add_argument(
        "command",
        choices=["start", "stop", "delete", "create"],
        help="Command to execute: start, stop, delete, create",
    )
    args = parser.parse_args()

    # Check Docker Compose version
    check_docker_compose_version()

    # Load environment variables from .env into the environment
    load_env_file("./docker/.env")

    # Perform actions based on the command
    if args.command == "start":
        detect_gpu_and_set_env()
        if platform.system() == "Darwin":
            start_ollama_serve()
        docker_compose_up()
    elif args.command == "stop":
        detect_gpu_and_set_env()
        docker_compose_down()
    elif args.command == "delete":
        detect_gpu_and_set_env()
        docker_compose_down()
        docker_delete_volumes()
    elif args.command == "create":
        detect_gpu_and_set_env()
        docker_compose_build()


if __name__ == "__main__":
    main()
