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

## Example: Leftovers Chef (using template)

From the examples above it may have become clear that all of these examples have a recurring structure and mainly come down to configuration. 

In order to make it easier for non-developers or frontend developers to set up new examples with minimal code interaction, you can **use a template structure** to easily define new example instances.

Let's give an overview of how to use the template to create the Leftovers Chef example.

### Copy the template files

To start a new project called "Leftovers Chef", first create new copies of the template files:

```bash
cp _example_template.py leftovers_chef.py
cp _config_template.py leftovers_chef_config.py
```

### Add configuration data

In the main script `leftovers_chef.py` you only need to update the import on line 15 with the name of the config file. That's all you need to do here, the main updates are isolated to the configuration file.

In the configuration file `leftovers_chef_config.py` you'll find a template with some dummy info that will help you configure the user input prompts and the cluster attributes they will populate, the initial propmpt for your example, the cluster name and description, the agents and the tasks. This is very similar to what happens in the [trip planner][trip_planner] and [IG post planner][ig_post_planner] examples.

### Add your example to the setup

When you've configured your example data, all that is left to do is to make sure you can run your example with the provided setup.

Add an import to `main.py`:
```python
from leftovers_chef import run_example as run_leftovers_chef_example
```
and add it to the supported examples map:
```python
EXAMPLES = {
    "trip_planner": run_trip_planner_example,
    "ig_post_planner": run_ig_post_planner_example,
    "cli_cluster": run_cli_cluster_example,
    # Add your example
    "leftovers_chef": run_leftovers_chef_example,
}
```

And lastly, add a `just` recipe to run your example in `example.just`:
```sh
# Runs an example that prompts the user for a description of their meal to prepare
[no-cd]
leftovers-chef:
    @__import__('os').system("just containers check")
    @__import__('os').system("docker exec -it examples /bin/bash -c \"source .venv/bin/activate && python examples/main.py leftovers_chef\"")
```

### Test it out!

Now test out your cluster by running:
```sh
just example leftovers_chef
```

### FAQ

> What about the requirements to use the template?

The requirements are the same as mentioned in [Environment Setup](#environment-setup). Nothing additional is required.

> Why are the prompts in the configuration file regular strings instead of template strings?

The strings are dynamically formatted into template strings in example script when the cluster attributes can be resolved.

> What are the pros and cons of using the template?

You should use the template if you don't want to customise any behaviour. For example if you're not technical, you can still use the template to create agents. In that case it's simply updating configuration. 

A downside is that you don't have the freedom to change anything. For example, if you wanted to add a frontend that delivers user input and displays the results of the cluster execution, you'll need to change the script you're using. You could create a new template for that!

### What's next?

To improve upon this example and keep learning, you could build:

- Add an agent / task that adds a sustainability score to each meal that is suggested.
- Use a tool to:
  - Create a generated image of the meal
  - Use a web search to find a list of meals
  - Find and integrate a 3rd party tool that estimates sustainability impact.
- Further automation to use templates
- Make a template that uses the Python backend to interact with a Javascript frontend
- many more

## Tools

Agents can use tools to enhance their capabilities. Please refer to the [`tools` README][tools_README]
for a list of available tools, and instructions on how to add new ones.

## Events

Events allow offchain systems to respond to onchain actions, automating tool execution and model inference based on specific triggers. Please refer to the [`events` README][events_README] for more details.

<!-- List of Links -->

[docker]: https://docs.docker.com/engine/install/
[just]: https://github.com/casey/just
[python]: https://www.python.org/downloads/
[tools_README]: ../offchain/tools/README.md
[events_README]: ../offchain/events/README.md
[ig_post_planner]: ./ig_post_planner.py
[trip_planner]: ./trip_planner.py
[cli_cluster]: ./cli_cluster.py
[design_cluster]: ../onchain/README.md#cluster
[leftovers_chef_config]: ./leftovers_chef_config.py
