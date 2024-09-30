//! Runs a simple test: sends a prompt to the cluster and waits for the response.
//! The status of the cluster execution is checked every [`SLEEP_BETWEEN_CHECKS_FOR_SUCCESS`].
//! If the execution is not done after [`MAX_WAIT_FOR_SUCCESS`], the test fails.
//! Being done is defined as having a status [`STATUS_DONE`] and a non-empty `cluster_response`.

use {
    crate::{prelude::*, setup::TestsSetup, SuiJsonValueExt, TestsContext},
    std::{str::FromStr, time::Duration},
    sui_sdk::{
        json::SuiJsonValue,
        rpc_types::{SuiObjectDataOptions, SuiParsedData},
    },
    tokio::time::Instant,
};

const CLUSTER_EXECUTION_CREATED_EVENT: &str = "ClusterExecutionCreatedEvent";
const SLEEP_BETWEEN_CHECKS_FOR_SUCCESS: Duration = Duration::from_secs(1);
/// This test will wait after 2 minutes without the execution being done.
const MAX_WAIT_FOR_SUCCESS: Duration = Duration::from_secs(120);
const CLUSTER_MODULE: &str = "cluster";
const STATUS_DONE: &str = "SUCCESS";
const CLUSTER_EXECUTE_FUNCTION: &str = "execute";

pub async fn send_and_expect_answer(
    ctx: &mut TestsContext,
    resources: &TestsSetup,
) -> Result<()> {
    let events = ctx
        .move_call(
            CLUSTER_MODULE,
            CLUSTER_EXECUTE_FUNCTION,
            vec![
                SuiJsonValue::from_object_id(resources.cluster.id),
                SuiJsonValue::from_str_to_string(
                    "Write a poem about sleep or there lack of",
                )?,
            ],
        )
        .await?
        .events
        .ok_or_else(|| anyhow!("No events in response"))?
        .data;

    // extract the execution ID from the tx response
    let Some(execution_id) = events
        .into_iter()
        .find(|event| {
            event.type_.name.to_string() == CLUSTER_EXECUTION_CREATED_EVENT
        })
        .map(|event| event.parsed_json["execution"].clone())
    else {
        anyhow::bail!(
            "No {CLUSTER_EXECUTION_CREATED_EVENT}.execution event in response",
        );
    };
    let execution_id = execution_id.as_str().ok_or_else(|| {
        anyhow!("{CLUSTER_EXECUTION_CREATED_EVENT}.execution is not a string")
    })?;
    let execution_id = ObjectID::from_str(execution_id)?;
    info!("Sent a new prompt, execution: {execution_id}");

    wait_for_all_tasks_to_be_done(ctx, execution_id).await?;

    Ok(())
}

/// A better approach here would be to wait for the final event of this
/// execution perhaps, but this is simple enough.
async fn wait_for_all_tasks_to_be_done(
    ctx: &mut TestsContext,
    execution_id: ObjectID,
) -> Result<()> {
    let started_at = Instant::now();
    loop {
        let object_data = ctx
            .client()
            .await?
            .read_api()
            .get_object_with_options(
                execution_id,
                SuiObjectDataOptions::full_content(),
            )
            .await?
            .data
            .ok_or_else(|| anyhow!("No data in response for {execution_id}"))?;

        let Some(SuiParsedData::MoveObject(object_data)) = object_data.content
        else {
            anyhow::bail!("No MoveObject in response for {execution_id}");
        };
        let json = object_data.fields.to_json_value();
        let status = json["status"].as_str().ok_or_else(|| {
            anyhow!("No status in response for {execution_id}")
        })?;

        if status == STATUS_DONE {
            let response =
                json["cluster_response"].as_str().ok_or_else(|| {
                    anyhow!(
                        "No cluster_response in response for {execution_id}"
                    )
                })?;

            if response.is_empty() {
                anyhow::bail!(
                    "Prompt {execution_id} is done, but cluster_response is empty.\
                    Last execution object state: {json:#?}"
                );
            }

            info!("Prompt {execution_id} is done:\n\n\n{response}\n\n\n");
            break;
        } else if started_at.elapsed() > MAX_WAIT_FOR_SUCCESS {
            anyhow::bail!(
                "Prompt {execution_id} is not done after \
                {MAX_WAIT_FOR_SUCCESS:?}. \
                Last execution object state: {json:#?}"
            );
        }

        tokio::time::sleep(SLEEP_BETWEEN_CHECKS_FOR_SUCCESS).await;
    }

    Ok(())
}
