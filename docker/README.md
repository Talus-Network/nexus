# README

## Infrastructure description

Local infra consists of following services

- sui
  - 4 validators
  - faucet
  - fullnode
- nexus
  - events
  - tools
  - examples
- ollama (only on windows and linux)

There are also couple startup services

- sui
  - build-suitools
    - builds a sui image to a tag specified in .env
  - build-genesis
    - runs generate.py to generate new sui genesis.blob and validator.yaml
  - publish-package
    - builds and publishes the nexus smart contracts from ./onchain directory
  - bootstrap-model
    - bootstraps a Llama model on the Sui blockchain by creating a node and the model using nexus_sdk, then saves their details for future use.

## Troubleshooting

If you encounter trouble building the `build-genesis` image, try switching the context to default.

`docker context use default`
