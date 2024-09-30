# "Object is not available for consumption"

You may encounter this error when working with Sui localnet.
In a nutshell, this means that some previous operation using this object, usually a `Coin`, has not finished correctly.
Typically this happens when you turn off the localnet and start it again.

To fix it, you can regenerate the localnet:

```bash
localnet regen
```

# "This query type is not supported by the full node"

Most likely you are using very different version of localnet with Suibase.
You need to pin the version in your Suibase.yml file.
See the command `just suibase-setup`.

# "Server returned an error status code: 500"

Try regenerating the localnet:

```bash
localnet regen
```
