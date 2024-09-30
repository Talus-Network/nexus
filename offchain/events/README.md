# Events

This directory contains the offchain event listener [sui_event.py][sui_event_py], which receives `RequestForCompletionEvent` events
emitted by agents executing onchain. It then calls their required tools and passes those results with the defined prompt
to inference of specified models.

Any hosted Talus node would contain the contents of the `events` directory to efficiently handle requests
to their nodes models and tools.

**Towards hosted inference for Talus**
In the future, nodes can be modified to run inference using other's compute. [offchain.py][offchain_py] could be modified
to call any compute host for inference. Currently, [offchain.py][offchain_py] contains `process()` which calls the
[main.py][main_py] route `/predict`.

To see available models/tools and define new ones, see the [`tools` README.md][tools_readme].

## How to run this

When you start this service it expects the following variables that can be set either as environment variables or with flags:

- `--packageid` (env `PACKAGE_ID`) (required): Package ID to filter events
- `--privkey` (env `SUI_PRIVATE_KEY`) (required): Sui private key
- `--modelownercapid` (env `MODEL_OWNER_CAP_ID`) (required): Model owner capability object ID to submit completions
- `--rpc` (default: `http://localhost:9000`): RPC URL
- `--ws` (default: `ws://localhost:9000`): WebSocket URL

<!-- References -->

[sui_event_py]: ./sui_event.py
[offchain_py]: ./offchain.py
[main_py]: ../tools/server/main.py
[tools_readme]: ../tools/README.md
