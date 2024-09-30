# Nexus smart contracts

This is the onchain part of Nexus.

## General structure

The Nexus Move contracts are organized into several modules, each responsible for a specific
aspect of the agentic framework:

1. [`node`][node]: Represents computational units that can run models inferences.
2. [`model`][model]: Defines LLM models that can be run on nodes.
3. [`agent`][model]: Represents intelligent agents that use models to perform tasks.
4. [`cluster`][cluster]: Manages groups of agents working together.
5. [`task`][task]: Defines unit of work within a cluster.
6. [`tool`][tool]: Represents utilities that agents can use to complete tasks.
7. [`prompt`][prompt]: Handles the creation and management of prompts for LLMs.

For a technical audience interested in building a client for Nexus or using it as a Move
dependency, the following section provides details about the design.

## Design

### `Node` to `Model` to `Agent`

Invoking machine learning models requires hardware.
Nexus describes a state machine that tells the hardware what to do, but the execution of the machine learning models happens on `Node`s off-chain.
Creating a `Node` object is the first step when interacting with Nexus.
Each computing unit is represented by this _owned_ object, meaning whichever wallet owns the `Node` object has exclusive rights to permit other entities to use it.
See the [`talus::node` module](./sources/node.move) to understand how to create a node and what information is shared with the network.

Once we have defined the computing unit, we need to represent the machine learning model that powers LLM inference.
At the moment, only a `Node` owner can create a new shared `Model` object.
Since it's a shared object, it means it can be referenced in anyone's transaction.
However, upon creation of `Model` the transaction sender receives an owned `ModelOwnerCap` object.
This is a common Move pattern to handle permissions.
The shared `Model` object is a wrapper around `ModelInfo` that contains the model's metadata.
See the [`talus::model` module](./sources/model.move) to understand how to create a model and what information is shared with the network.
With `ModelInfo` one can create agents as is shown in the next step.
There are two paths to get access to the `ModelInfo`:

1. The model owner can get it from the `Model` object by showing the `ModelOwnerCap`.
2. The model owner can issue `ModelInferencePromise` and transfer it to another wallet.
   Such wallet can then use the `ModelInferencePromise` to get the `ModelInfo`.

These access patterns enable the model owner to control who can use the model.
Note the name `ModelInferencePromise`.
At the moment, we don't have any punishment system for slashing inference providers that don't deliver the result.
Hence, for now, the model owner only makes a promise to whoever wants to use the model that the inference will be done.

Finally, we have the `Agent` object which is a wrapper around `AgentBlueprint` object similarly to `Model` and `ModelInfo`.
Upon creation of an `Agent` object, the transaction sender receives an owned `AgentOwnerCap` object.
See the [`talus::agent` module](./sources/agent.move) to understand how to create an agent and what information is shared with the network.

An agent uses an LLM (the `Model`) for a specific narrower set of goals.
One node can run multiple models, and one model can be used by multiple agents.
Two agents with different roles are expected to still use the same model.

### Cluster

Agents can be combined into a `Cluster` object.
A `Cluster` also defines tasks to be performed by those agents.
(The simplest cluster that's runnable has one agent performing one task.)
When a `Cluster` is created, the creator receives a `ClusterOwnerCap` object.
With this object they can add tasks to the cluster.
They can also add agents to the cluster, either ones they created themselves (provided they have access to the `ModelInfo` via `ModelOwnerCap` or `ModelInferencePromise`) or agents created by others.

However, agent owners have control over their agents.
To add someone else's agent, the cluster owner needs to have `AgentRosterPromise` for that agent.
They can only obtain it from the agent owner.
This is the same pattern we saw with the `ModelInferencePromise`.

An example of a cluster is given in the [`talus::cluster_tests` module](./sources/tests/cluster_tests.move).

Once the `Cluster` has been defined, users can submit their prompt that will be fed into the LLM of the agent owning the first task in the cluster.
This process creates `ClusterExecution` shared object which copies the `Cluster` blueprint and tracks the state of a particular user execution.
Multiple users can submit their prompts to the same cluster, having each their own `ClusterExecution` object.
See the [`talus::cluster::execute` entry function](./sources/cluster.move).

Creating a new `ClusterExecution` emits a `RequestForCompletionEvent` event.
Nodes listen to these events and filter them based on IDs of models they run.
Once the node that runs the LLM inference for the first agent has finished its off-chain computation, it submits the result to the particular `ClusterExecution` object.
It submits the result via either

- `submit_completion_as_node_owner`,
- `submit_completion_as_model_owner` or
- `submit_completion_as_cluster_owner`.

The specific function depends on the off-chain node implementation and only differs in the way permissions are checked.

All LLM output is stored on-chain.
If there are more than one task, the process repeats.
The completion submission emits `RequestForCompletionEvent` which leads to a (possibly different) node again feeding the string in the `RequestForCompletionEvent.prompt_contents` property to the LLM and submitting the result via one of the aforementioned functions.

Once all tasks are done, the `ClusterExecution` object is marked as completed by setting appropriate value of its `status` property.

### Tools

Tools are defined on `ClusterBlueprint` level, specifically on a task.
Each task can optionally have a tool name and a list of parameters.
At the moment we make the assumption that the cluster owner defines only tools which the nodes that run agents know how to use.

The off-chain listener then first matches the tool name to a function to execute.
The output of the function is appended to the prompt that is fed to the LLM.
LLM response is then submitted in the aforementioned completion flow.

<!-- List of References -->

[gdoc-next-steps]: https://docs.google.com/document/d/1pWrayUt3zI1YQqnzR6MqLDYwz-x7i845WAGv9im0fis
[gdoc-user-stories]: https://docs.google.com/document/d/1zf-NdrW6bSCmmVWuKvM8rqG1s2KwxlcPfrjwwHxzXzU
[git-main]: https://github.com/Talus-Network/ai/tree/f64e92638

[node]: ./sources/node.move
[model]: ./sources/model.move
[agent]: ./sources/agent.move
[cluster]: ./sources/cluster.move
[task]: ./sources/task.move
[tool]: ./sources/tool.move
[prompt]: ./sources/prompt.move
