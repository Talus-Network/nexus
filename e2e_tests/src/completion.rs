//! We listen to emitted events named [`REQ_FOR_COMPLETION_EVENT`] in the [`PROMPT_MODULE`].
//! Then we run the LLM with the given input read from the event and wait for its completion.
//! Finally, we submit the completion result to the chain.

use {
    crate::{prelude::*, setup::TestsSetup, TestsContext},
    futures_util::StreamExt,
    serde::Deserialize,
    serde_json::json,
    std::str::FromStr,
    sui_sdk::{
        json::SuiJsonValue,
        rpc_types::{EventFilter, SuiEvent},
    },
};

const CLUSTER_MODULE: &str = "cluster";
const CLUSTER_SUBMIT_COMPLETION_FUNCTION: &str =
    "submit_completion_as_cluster_owner";
const PROMPT_MODULE: &str = "prompt";
const REQ_FOR_COMPLETION_EVENT: &str = "RequestForCompletionEvent";

/// This is the JSON that we expect to capture.
/// There are more fields on this event but for now we only care about these.
#[derive(Deserialize)]
struct RequestForCompletionEvent {
    /// Cluster execution ID
    cluster_execution: String,
    /// Model ID
    model: String,
    /// The model name that should complete
    model_name: String,
    /// What the model should complete
    prompt_contents: String,
    /// If attached, we execute the tool and attach the output to the
    /// LLM prompt.
    tool: Option<ToolObject>,
}

/// As returned by Sui APIs.
#[derive(Deserialize)]
struct ToolObject {
    fields: Tool,
}

/// As defined in the smart contract.
#[derive(Deserialize)]
struct Tool {
    name: String,
    args: Vec<String>,
}

/// Starts listening to the [`REQ_FOR_COMPLETION_EVENT`] events and completes
/// them using the Ollama API in a separate task.
pub(crate) async fn spawn_task(
    mut ctx: TestsContext,
    resources: TestsSetup,
) -> Result<()> {
    debug!("Creating stream of Sui events {REQ_FOR_COMPLETION_EVENT}");

    // filter for the event type we are interested in
    // ideally we'd also filter by the event's data, but this event filter is
    // currently broken in the Sui SDK
    let mut stream = ctx
        .client()
        .await?
        .event_api()
        .subscribe_event(EventFilter::MoveEventType(FromStr::from_str(
            &format!(
                "{pkg_id}::{PROMPT_MODULE}::{REQ_FOR_COMPLETION_EVENT}",
                pkg_id = ctx.pkg_id,
            ),
        )?))
        .await?;

    tokio::spawn(async move {
        while let Some(event_res) = stream.next().await {
            let event_json = match event_res {
                Ok(SuiEvent { parsed_json, .. }) => parsed_json,
                Err(err) => {
                    error!(
                        "Error while listening to \
                            {REQ_FOR_COMPLETION_EVENT}: {err}"
                    );
                    break;
                }
            };

            if let Err(err) =
                submit_for_event(&mut ctx, &resources, event_json).await
            {
                error!("Error submitting completion: {err}");
            };
        }
    });

    Ok(())
}

async fn submit_for_event(
    ctx: &mut TestsContext,
    resources: &TestsSetup,
    event_json: JsonValue,
) -> Result<()> {
    let RequestForCompletionEvent {
        cluster_execution,
        model,
        mut prompt_contents,
        model_name,
        tool,
    } = serde_json::from_value(event_json.clone()).map_err(|err| {
        anyhow!(
            "Failed to parse {REQ_FOR_COMPLETION_EVENT} event\n\
            {event_json:#?}\n\nError: {err}"
        )
    })?;

    let expected_model_id = resources.model.id;
    if expected_model_id != ObjectID::from_str(&model)? {
        // not an event that we are supposed to handle
        return Ok(());
    }

    if let Some(ToolObject {
        fields: Tool { name, args },
        ..
    }) = tool
    {
        match name.as_str() {
            // here we could implement some tool execution
            "some_tool" => {
                prompt_contents +=
                    &format!("\n\nInvoked some tool with args:\n{args:#?}",);
            }
            unknown_tool => warn!(
                "Execution '{cluster_execution}' \
                asked for an unknown tool: {unknown_tool}"
            ),
        };
    }

    // talk to ollama via HTTP API
    let client = reqwest::Client::new();
    let res = client
        .post(ctx.ollama_http_api.clone())
        .json(&json!({
            "model": model_name,
            "prompt": prompt_contents,
        }))
        .send()
        .await?;

    if !res.status().is_success() {
        error!(
            "Failed to get completion from ollama: {}\n\n{:?}",
            res.status(),
            res.text().await
        );
        return Ok(());
    }

    let mut completion = String::with_capacity(1024);
    for line in res
        .text()
        .await?
        .lines()
        .map(|l| l.trim())
        .filter(|l| !l.is_empty())
    {
        #[derive(Deserialize)]
        struct OllamaResponseLine {
            response: String,
            done: bool,
        }

        let OllamaResponseLine { response, done } = serde_json::from_str(line)?;

        if done {
            break;
        }

        completion.push_str(&response);
    }

    let cluster_execution = ObjectID::from_str(&cluster_execution)?;
    // this could happen in a separate task and the listener can run another
    // completion meanwhile already
    let resp = ctx
        .move_call(
            CLUSTER_MODULE,
            CLUSTER_SUBMIT_COMPLETION_FUNCTION,
            vec![
                SuiJsonValue::from_object_id(cluster_execution),
                SuiJsonValue::from_object_id(resources.cluster.owner_cap),
                SuiJsonValue::new(JsonValue::String(completion))?,
            ],
        )
        .await?;

    info!(
        "Submitted completion for model '{model_name}' and cluster execution \
        '{cluster_execution}' in tx {}",
        resp.digest
    );

    Ok(())
}
