
set shell := [ "python3", "-c"]

[private]
default: version-check
   @__import__('os').system("just -l")

[private]
version-check:
    @import sys; major, minor = sys.version_info[:2]; \
    assert (major, minor) >= (3, 7), "This script requires at least Python 3.7. Please link \"python3\" to Python 3.7 or higher and try again."
    
# Commands for running examples
mod example 'examples/example.just'

# Build, Start, Stop, or Clean Up docker containers
mod containers 'docker/containers.just'

# Builds and starts the entire environment
infra-up: version-check
    @print("Building and starting the entire environment..."); __import__('os').system("just containers build"); __import__('os').system("just containers start")

# Shuts down and cleans up the environment
infra-down: version-check
    @print("Stopping and cleaning up the entire environment..."); __import__('os').system("just containers stop"); __import__('os').system("just containers clean")
