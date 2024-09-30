This binary setups dummy node, model, agent and cluster.

Then it creates a test prompt (and therefore cluster execution) and calls ollama (or a mocked API) to generate completions for submitted prompts.

The purpose of this code is to test Nexus with specific scenarios.
Currently we use it in [CI](../.github/workflows/talus-agentic-framework.yml).

# Run

Check your active environment and make sure it's `localnet`.
For example

```bash
$ sui client active-env
```

Have Sui localnet running.
For example, with the Sui CLI you can run

```bash
$ sui start
```

Optionally, have Ollama running with `mistras` model.
For example

```bash
$ ollama run mistral
```

Ollama http APIs are optional because they are mocked in the test binary itself if the HTTP endpoint is not provided.
This is useful for example if you want to test some change and are not interested in the completions themselves.
CI is using the mocked API as well.

This test binary expects some env vars.
These can be directly set to the environment or set in a `.env` file.

```
RUST_LOG=info
FW_PKG_ID=...
SUI_WALLET_PATH=~/.sui/sui_config/client.yaml
OLLAMA_HTTP_API=http://localhost:11434/api/generate
```

`FW_PKG_ID` will be the package id of the framework package that you want to test.
It must be deployed in the Sui localnet.
For example, you can deploy the package with

```bash
$ cd onchain
$ sui client publish --skip-dependency-verification
```

This command spits out package ID that you can set to that env var.

`SUI_WALLET_PATH` must point to an existing yaml file with your local wallet.

As mentioned before, `OLLAMA_HTTP_API` is optional and will be mocked if empty.

Now you should be good to go to `cargo run`.

There's a oneclick test script [`oneclick-test.sh`](./oneclick-test.sh) that sets up the environment and runs the test binary.
It emulates what happens in CI.
