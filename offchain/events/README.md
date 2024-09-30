# Events

This package contains the offchain event listener (`sui_event.py`), which receives `RequestForCompletionEvent` events
emitted by agents executing onchain. It then calls their required tools and passes those results with the defined prompt
to inference of specified models.

To see available models/tools and define new ones, see the [`tools` README.md][tools_readme].

## How to run this

When you start this service it expects the following variables that can be set either as environment variables or with flags:

- `--packageid` (env `PACKAGE_ID`) (required): Package ID to filter events
- `--privkey` (env `SUI_PRIVATE_KEY`) (required): Sui private key
- `--modelownercapid` (env `MODEL_OWNER_CAP_ID`) (required): Model owner capability object ID to submit completions
- `--rpc` (default: `http://localhost:9000`): RPC URL
- `--ws` (default: `ws://localhost:9000`): WebSocket URL

<!-- References -->

[tools_readme]: ../tools/README.md
