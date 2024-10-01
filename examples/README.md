# Examples

We have built a few examples to showcase Nexus agents.

Before you can use the examples or build your own agents, you need to install a few things first,
as shown in the next section.

When you run either of the examples, you will be prompted to start two services:

- [`tools`][tools_README] which you need to start only once for all examples, and
- [`events`][events_README] which you need to start for each example anew and once the example finished, you can stop it.

You will be given exact instructions on how to start and stop these services when you run either example.

- [Examples](#examples)
  - [Environment setup](#environment-setup)
    - [Operating System](#operating-system)
    - [Helper tools](#helper-tools)
    - [Operating System packages](#operating-system-packages)
    - [Python and virtual environment](#python-and-virtual-environment)
    - [Suibase](#suibase)
    - [`PATH`](#path)
    - [Ollama](#ollama)
  - [Example: Instagram Post Planner](#example-instagram-post-planner)
  - [Example: Trip Planner](#example-trip-planner)
  - [Example: CLI Cluster](#example-cli-cluster)
  - [Tools](#tools)

## Environment setup

### Operating System

We assume Ubuntu `22.04 LTS`.

### Helper tools

You need to install the following tools by following their official installation instructions:

- [`cargo`][cargo]
- [`just`][just] (on Linux install it with "Pre-Built Binaries" rather than with `apt` because of an outdated version)
- [`uv`][uv]

We use `just` as a general command runner, and `uv` to manage Python and virtual environments
(`.venv`). The [`justfile`][justfile] contains installation instructions for everything we
describe here, and you can run `just` from this folder, as it will automatically discover the
`justfile` at the top level.

### Operating System packages

You can install dependencies with `just apt-setup`.

### Python and virtual environment

We install and use Python `3.10`.

From inside the working copy of the repository, run `just venv-setup` to:

- install Python,
- create the necessary `.venv`,
- install all the needed dependencies in the `.venv`.

### Suibase

Talus smart contracts are written in Sui Move, and until our testnet is ready we use a
compatible (from the Sui Move point of view) chain, based on [`Suibase`][suibase].

You can download and install Suibase with `just suibase-setup`.

> [!NOTE]
> Our setup script pins localnet to a particular version in `~/suibase/workdirs/localnet/suibase.yaml`

### `PATH`

Make sure `~/.local/bin` is in your `PATH`. Suibase requires this, as it installs its
executables there.

### Ollama

For the LLM component we install and use [Ollama][ollama] with the `llama3.2:1b` model. You can
install both with `just ollama-setup`.

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

<!-- List of Links -->

[cargo]: https://doc.rust-lang.org/cargo/getting-started/installation.html
[just]: https://github.com/casey/just
[uv]: https://github.com/astral-sh/uv
[suibase]: https://suibase.io/
[ollama]: https://ollama.com/
[tools_README]: ../offchain/tools/README.md
[events_README]: ../offchain/events/README.md
[ig_post_planner]: ./ig_post_planner.py
[trip_planner]: ./trip_planner.py
[cli_cluster]: ./cli_cluster.py
[justfile]: ../justfile
[design_cluster]: ../onchain/README.md#cluster
