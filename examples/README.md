# Examples

We have built a few examples to showcase Nexus agents.

Before you can use the examples or build your own agents, you need to install a few things first,
as shown in the next section.

- [Examples](#examples)
  - [Environment setup](#environment-setup)
    - [Operating System](#operating-system)
    - [Helper tools](#helper-tools)
    - [Docker](#docker)
  - [Example: Instagram Post Planner](#example-instagram-post-planner)
  - [Example: Trip Planner](#example-trip-planner)
  - [Example: CLI Cluster](#example-cli-cluster)
  - [Tools](#tools)
  - [Events](#events)

## Environment setup

### Operating System

We support macOS, windows and linux.

### Helper tools

You need to install the following tools by following their official installation instructions:

- [`docker`][docker]
- [`just`][just] (on Linux install it with "Pre-Built Binaries" rather than with `apt` because of an outdated version)
- [`python`][python]
- [`ollama`][ollama] (installed automatically)

We use `just` as a general command runner, just run `just` for available commands.

### Docker

We use Docker to create a consistent local environment for all examples, ensuring compatibility across macOS, Windows, and Linux. By packaging dependencies into isolated containers, we aim to provide a uniform environment that minimizes compatibility issues. To run these examples, you’ll need Docker Compose version 2.20 or higher.

**Note for macOS users:** While Ollama can run in a container on macOS, it experiences poor performance due to Docker Desktop for macOS lacking GPU acceleration support. To ensure better performance, Ollama is running directly on the host instead of within a container.

## Example: Instagram Post Planner

This [example][ig_post_planner] demonstrates how to create an Instagram post planner agent using
the Nexus SDK.

Run with `just example ig-post-planner`.

## Example: Trip Planner

This [example][trip_planner] demonstrates how to create a trip planner agent using the Nexus
SDK.

Run with `just example trip-planner`.

## Example: CLI Cluster

This [example][cli_cluster] prompts the user to create a [cluster][design_cluster] by describing
agents and tasks on the command line.

Run with `just example cli-cluster`.

## Tools

Agents can use tools to enhance their capabilities. Please refer to the [`tools` README][tools_README]
for a list of available tools, and instructions on how to add new ones.

## Events

Events allow offchain systems to respond to onchain actions, automating tool execution and model inference based on specific triggers. Please refer to the [`events` README][events_README] for more details.

<!-- List of Links -->

[docker]: https://docs.docker.com/engine/install/
[just]: https://github.com/casey/just
[ollama]: https://ollama.com/
[python]: https://www.python.org/downloads/
[tools_README]: ../offchain/tools/README.md
[events_README]: ../offchain/events/README.md
[ig_post_planner]: ./ig_post_planner.py
[trip_planner]: ./trip_planner.py
[cli_cluster]: ./cli_cluster.py
[design_cluster]: ../onchain/README.md#cluster
