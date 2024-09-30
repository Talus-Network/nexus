//! This is an executable that runs an e2e test for Nexus
//! Move package.
//!
//! It assumes
//! - Sui localnet running
//! - deployed Nexus package
//! - env var [`env_vars::FW_PKG_ID`] with the ID of the Nexus package
//! - env var [`env_vars::SUI_WALLET_PATH`] with a filesystem path to Sui wallet configuration
//! - Sui wallet configured to localnet
//! - at least 1 SUI in an owned `Coin<SUI>`
//!
//! Optionally
//! - Env var [`env_vars::OLLAMA_HTTP_API`] with reachable URL of the Ollama HTTP API
//!   following [this specs][ollama-http-api].
//!   If not provided then a mock server is started.
//!
//! We setup resources such as node, model, agent and cluster.
//! This happens in [setup].
//! Then, we start listening for requests and connect them to the Ollama API.
//! This happens in [completion].
//! And finally we regularly send prompts to the cluster.
//! This happens in [prompt].
//!
//! The tools are not executed in this test.
//! One tool is set up for the test cluster and we parse the tool from the Sui
//! event that is listened to by the [completion] module.
//! However, as of now the tool is mocked.
//!
//! [ollama-http-api]: https://github.com/ollama/ollama/blob/main/docs/api.md

mod completion;
mod ollama_mock;
mod prelude;
mod prompt;
mod setup;

use {
    prelude::*,
    std::{env, path::PathBuf, str::FromStr, sync::Arc},
    sui_sdk::{
        json::SuiJsonValue,
        rpc_types::{
            SuiObjectData,
            SuiObjectDataOptions,
            SuiTransactionBlockResponse,
        },
        types::{
            base_types::{ObjectRef, SuiAddress},
            transaction::{ProgrammableTransaction, TransactionData},
        },
    },
    tokio::sync::Mutex,
};

const REQUIRED_SUI_ENV: &str = "localnet";
const GAS_BUDGET: u64 = 10_000_000_000;

mod env_vars {
    pub(super) const SUI_WALLET_PATH: &str = "SUI_WALLET_PATH";
    pub(super) const FW_PKG_ID: &str = "FW_PKG_ID";
    pub(super) const OLLAMA_HTTP_API: &str = "OLLAMA_HTTP_API";
}

#[derive(Clone)]
struct TestsContext {
    wallet: Arc<Mutex<WalletContext>>,
    pkg_id: ObjectID,
    me: SuiAddress,
    ollama_http_api: reqwest::Url,
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenvy::dotenv().ok();

    env_logger::init();

    let mut ctx = TestsContext::from_env().await?;

    let resources = setup::test(&mut ctx).await?;

    info!(
        "\
        Resources successfully set up\n\
        Node   : {node}\n\
        Model  : {model}\n\
        Agent  : {agent}\n\
        Cluster   : {cluster}\n\
    ",
        node = resources.node,
        model = resources.model.id,
        agent = resources.agent.id,
        cluster = resources.cluster.id,
    );

    completion::spawn_task(ctx.clone(), resources.clone()).await?;

    prompt::send_and_expect_answer(&mut ctx, &resources).await?;

    info!("All done");
    Ok(())
}

impl TestsContext {
    async fn from_env() -> Result<Self> {
        let ollama_http_api = if let Some(http_api) =
            env::var(env_vars::OLLAMA_HTTP_API)
                .ok()
                .filter(|s| !s.is_empty())
        {
            FromStr::from_str(&http_api)?
        } else {
            info!(
                "Env var {} missing, starting mock server",
                env_vars::OLLAMA_HTTP_API
            );
            ollama_mock::start().await?
        };

        let pkg_id = ObjectID::from_str(
            &env::var(env_vars::FW_PKG_ID).map_err(|_| {
                anyhow!(
                    "Env var {} missing.\n\
                    You need to publish the Sui package \
                    and set the resulting ID to this env var.\n\
                    You can also store the ID in an .env file",
                    env_vars::FW_PKG_ID
                )
            })?,
        )?;

        let wallet_path = PathBuf::from(
            env::var(env_vars::SUI_WALLET_PATH).map_err(|_| {
                anyhow!(
                    "Env var {} missing.\n\
                    You must provide a path to the Sui wallet configuration, \
                    typically at ~/.sui/sui_config/client.yaml.\n\
                    If you don't have this file, you can create it by running \
                    'sui genesis'.\n\
                    You can also store the path in an .env file",
                    env_vars::SUI_WALLET_PATH
                )
            })?,
        );
        let mut wallet = WalletContext::new(&wallet_path, None, None)?;

        if wallet.config.active_env != Some(REQUIRED_SUI_ENV.to_string()) {
            anyhow::bail!("This test requires {REQUIRED_SUI_ENV}");
        }
        let active_env = wallet
            .config
            .envs
            .iter_mut()
            .find(|env| env.alias == REQUIRED_SUI_ENV)
            .ok_or_else(|| anyhow!("No env with alias {REQUIRED_SUI_ENV}"))?;
        if active_env.ws.is_none() {
            // if WS endpoint is missing, we assume it as in localnet it's pretty
            // much the same as RPC with just the protocol changed
            active_env.ws = Some(active_env.rpc.replace("http", "ws"));
        }

        Ok(Self {
            me: wallet.active_address()?,
            wallet: Arc::new(Mutex::new(wallet)),
            pkg_id,
            ollama_http_api,
        })
    }

    async fn client(&self) -> Result<SuiClient> {
        self.wallet.lock().await.get_client().await
    }

    async fn find_sui_coin(&self) -> Result<ObjectRef> {
        let sui_coin = None; // the default is SUI
        let two_sui = 2_000_000_000;
        let coins = self
            .client()
            .await?
            .coin_read_api()
            .select_coins(self.me, sui_coin, two_sui, vec![])
            .await?;

        coins
            .first()
            .map(|c| (c.coin_object_id, c.version, c.digest))
            .ok_or_else(|| anyhow!("No SUI coins found for the addr"))
    }

    async fn move_call(
        &self,
        module: &str,
        function: &str,
        call_args: Vec<SuiJsonValue>,
    ) -> Result<SuiTransactionBlockResponse> {
        let tx = self
            .client()
            .await?
            .transaction_builder()
            .move_call(
                self.me,
                self.pkg_id,
                module,
                function,
                vec![],
                call_args,
                None, // auto pick coin
                GAS_BUDGET,
                None,
            )
            .await?;

        let wallet = self.wallet.lock().await;
        let signed_tx = wallet.sign_transaction(&tx);
        let resp = wallet.execute_transaction_must_succeed(signed_tx).await;

        debug!("Call to {module}::{function}: {}", resp.digest);

        Ok(resp)
    }

    async fn execute_ptx(
        &mut self,
        tx: ProgrammableTransaction,
    ) -> Result<SuiTransactionBlockResponse> {
        let coin = self.find_sui_coin().await?;

        let gas_price = self
            .client()
            .await?
            .read_api()
            .get_reference_gas_price()
            .await?;
        let tx = TransactionData::new_programmable(
            self.me,
            vec![coin],
            tx,
            GAS_BUDGET,
            gas_price,
        );

        let wallet = self.wallet.lock().await;
        let signed_tx = wallet.sign_transaction(&tx);
        let resp = wallet.execute_transaction_must_succeed(signed_tx).await;

        debug!("Call to programmable tx: {}", resp.digest);

        Ok(resp)
    }

    /// Returns [`ObjectRef`] for the object with the given ID.
    /// That's useful for programmable txs.
    async fn get_object_ref(&self, id: ObjectID) -> Result<ObjectRef> {
        let SuiObjectData {
            version, digest, ..
        } = self
            .client()
            .await?
            .read_api()
            .get_object_with_options(id, SuiObjectDataOptions::full_content())
            .await?
            .data
            .ok_or_else(|| anyhow!("Object {id} not found"))?;

        Ok((id, version, digest))
    }
}

trait SuiJsonValueExt
where
    Self: Sized,
{
    fn from_str_to_string(s: &str) -> Result<Self>;
}

impl SuiJsonValueExt for SuiJsonValue {
    fn from_str_to_string(s: &str) -> Result<Self> {
        SuiJsonValue::new(JsonValue::String(s.to_string()))
    }
}
