//! The first step of the tests is to setup all required resources on chain.
//! The resources are defined in the [`TestsSetup`] struct.

use {
    crate::{prelude::*, SuiJsonValueExt, TestsContext},
    std::str::FromStr,
    sui_sdk::{
        json::SuiJsonValue,
        types::{
            programmable_transaction_builder::ProgrammableTransactionBuilder,
            transaction::ObjectArg,
            Identifier,
        },
    },
};

const AGENT_CREATE_AND_SHARE_FUNCTION: &str = "create_and_share";
const AGENT_CREATED_EVENT: &str = "AgentCreatedEvent";
const AGENT_GET_BLUEPRINT_FUNCTION: &str = "get_blueprint";
const AGENT_MODULE: &str = "agent";
const AGENT_NAME: &str = "my-agent-1";
const CLUSTER_ADD_AGENT_FUNCTION: &str = "add_agent";
const CLUSTER_ADD_TASK_ENTRY_FUNCTION: &str = "add_task_entry";
const CLUSTER_ATTACH_TASK_TOOL_FUNCTION: &str = "attach_tool_to_task_entry";
const CLUSTER_CREATE_FUNCTION: &str = "create";
const CLUSTER_CREATED_EVENT: &str = "ClusterCreatedEvent";
const CLUSTER_MODULE: &str = "cluster";
const MODEL_CREATE_FUNCTION: &str = "create";
const MODEL_CREATED_EVENT: &str = "ModelCreatedEvent";
const MODEL_GET_INFO_FUNCTION: &str = "get_info";
const MODEL_MODULE: &str = "model";
const MODEL_NAME: &str = "mistral";
const NODE_CREATE_FUNCTION: &str = "create";
const NODE_CREATED_EVENT: &str = "NodeCreatedEvent";
const NODE_MODULE: &str = "node";

#[derive(Debug, Clone)]
pub(crate) struct TestsSetup {
    pub(crate) node: ObjectID,
    pub(crate) model: TestModel,
    pub(crate) agent: TestAgent,
    pub(crate) cluster: TestCluster,
}

#[derive(Debug, Clone)]
pub(crate) struct TestModel {
    pub(crate) id: ObjectID,
    pub(crate) owner_cap: ObjectID,
}

#[derive(Debug, Clone)]
pub(crate) struct TestAgent {
    pub(crate) id: ObjectID,
    pub(crate) owner_cap: ObjectID,
}

#[derive(Debug, Clone)]
pub(crate) struct TestCluster {
    pub(crate) id: ObjectID,
    pub(crate) owner_cap: ObjectID,
}

/// Tests setup functionality of the Talus framework.
/// The resulting test resources will be used later in the tests.
pub(crate) async fn test(ctx: &mut TestsContext) -> Result<TestsSetup> {
    info!("Setting up a node");
    let node = create_node(ctx).await?;

    info!("Setting up a model");
    let model = create_model_with_owner_cap(ctx, node).await?;

    info!("Setting up an agent");
    let agent = create_agent(ctx, &model).await?;

    info!("Setting up a cluster");
    let cluster = create_cluster_with_owner_cap(ctx).await?;

    info!("Adding agent to the cluster");
    add_agent_to_cluster(ctx, &agent, &cluster).await?;

    info!("Adding tasks to the cluster");
    // tasks as defined in the `cluster_tests.move`
    add_task_to_cluster(
        ctx,
        &cluster,
        TaskDefinition {
            task_name: "Analyze Poem Request",
            agent_name: AGENT_NAME,
            description: "Analyze the user's request for poem creation",
            expected_output: "A structured analysis of the poem request",
            prompt: "Analyze the user's input for poem style and subject. \
                If either is missing, prepare an error message.",
            tool: Some(ToolDefinition {
                tool_name: "some_tool",
                args: &["arg1", "arg2"],
            }),
            ..Default::default()
        },
    )
    .await?;
    add_task_to_cluster(
        ctx,
        &cluster,
        TaskDefinition {
            task_name: "Create Poem",
            agent_name: AGENT_NAME,
            description: "Create a poem based on the analyzed request",
            expected_output: "A poem matching the user's requirements",
            prompt: "Create a poem based on the provided style and subject. \
                Be creative and inspiring.",
            ..Default::default()
        },
    )
    .await?;

    Ok(TestsSetup {
        node,
        model,
        agent,
        cluster,
    })
}

/// Sets up a new dummy node.
/// This node will be an owned object of the wallet.
async fn create_node(ctx: &mut TestsContext) -> Result<ObjectID> {
    let events = ctx
        .move_call(
            NODE_MODULE,
            NODE_CREATE_FUNCTION,
            vec![
                // name: String
                SuiJsonValue::from_str_to_string("my-node-1")?,
                // node_type: String,
                SuiJsonValue::from_str_to_string("some-type")?,
                // gpu_memory: u64,
                SuiJsonValue::from_str_to_string("16")?,
                // image_hash: vector<u8>,
                SuiJsonValue::new(JsonValue::Array(vec![]))?,
                // external_arguments: vector<u8>,
                SuiJsonValue::new(JsonValue::Array(vec![]))?,
            ],
        )
        .await?
        .events
        .ok_or_else(|| {
            anyhow!(
                "No events found in the response of create node transaction"
            )
        })?
        .data;

    let Some(node_id) = events
        .into_iter()
        .find(|event| event.type_.name.to_string() == NODE_CREATED_EVENT)
        .map(|event| event.parsed_json["node"].clone())
    else {
        anyhow::bail!(
            "No {NODE_CREATED_EVENT}.node found \
            in the response of create node transaction"
        )
    };

    let node_id_str = node_id
        .as_str()
        .ok_or_else(|| anyhow!("{NODE_CREATED_EVENT}.node is not a string"))?;

    Ok(ObjectID::from_str(node_id_str)?)
}

/// Sets up a new dummy model.
/// Returns model ID and model owner capability ID.
async fn create_model_with_owner_cap(
    ctx: &mut TestsContext,
    node: ObjectID,
) -> Result<TestModel> {
    let events = ctx
        .move_call(
            MODEL_MODULE,
            MODEL_CREATE_FUNCTION,
            vec![
                // node: &Node
                SuiJsonValue::from_object_id(node),
                // name: String
                SuiJsonValue::from_str_to_string(MODEL_NAME)?,
                // model_hash: vector<u8>
                SuiJsonValue::new(JsonValue::Array(vec![JsonValue::Number(
                    1.into(),
                )]))?,
                // url: String
                SuiJsonValue::from_str_to_string("https://example.com")?,
                // token_price: u64
                SuiJsonValue::from_str_to_string("100")?,
                // capacity: u64
                SuiJsonValue::from_str_to_string("1")?,
                // num_params: u64
                SuiJsonValue::from_str_to_string("1")?,
                // description: String
                SuiJsonValue::from_str_to_string("This is my test model")?,
                // max_context_length: u64
                SuiJsonValue::from_str_to_string("2048")?,
                // is_fine_tuned: bool
                SuiJsonValue::new(JsonValue::Bool(true))?,
                // family: String
                SuiJsonValue::from_str_to_string("my-family")?,
                // vendor: String
                SuiJsonValue::from_str_to_string("my-vendor")?,
                // is_open_source: bool
                SuiJsonValue::new(JsonValue::Bool(true))?,
                // datasets: vector<String>
                SuiJsonValue::new(JsonValue::Array(vec![]))?,
            ],
        )
        .await?
        .events
        .ok_or_else(|| {
            anyhow!(
                "No events found in the response of create model transaction"
            )
        })?
        .data;

    let Some(event_json) = events
        .into_iter()
        .find(|event| event.type_.name.to_string() == MODEL_CREATED_EVENT)
        .map(|event| event.parsed_json.clone())
    else {
        anyhow::bail!(
            "No {MODEL_CREATED_EVENT} found in \
            the response of create model transaction"
        )
    };

    let model_id_str = event_json["model"].as_str().ok_or_else(|| {
        anyhow!("{MODEL_CREATED_EVENT}.model is not a string")
    })?;
    let model_owner_cap_id_str =
        event_json["owner_cap"].as_str().ok_or_else(|| {
            anyhow!("{MODEL_CREATED_EVENT}.owner_cap is not a string")
        })?;

    Ok(TestModel {
        id: ObjectID::from_str(model_id_str)?,
        owner_cap: ObjectID::from_str(model_owner_cap_id_str)?,
    })
}

/// Sets up a new dummy agent.
/// Since we already created a model that we _own_ we can create the agent
/// without a model inference promise.
async fn create_agent(
    ctx: &mut TestsContext,
    model: &TestModel,
) -> Result<TestAgent> {
    let owner_cap_ref = ctx.get_object_ref(model.owner_cap).await?;
    let (_, model_version, _) = ctx.get_object_ref(model.id).await?;

    // In this programmable tx we will first get the ModelInfo with our
    // owner cap.
    // Then we use the model info to create an agent.
    let mut ptb = ProgrammableTransactionBuilder::new();

    let model_arg = ptb.obj(ObjectArg::SharedObject {
        id: model.id,
        initial_shared_version: model_version,
        mutable: false,
    })?;

    let model_owner_cap_arg =
        ptb.obj(ObjectArg::ImmOrOwnedObject(owner_cap_ref))?;

    let model_info_arg = ptb.programmable_move_call(
        ctx.pkg_id,
        Identifier::new(MODEL_MODULE)?,
        Identifier::new(MODEL_GET_INFO_FUNCTION)?,
        vec![],
        vec![model_arg, model_owner_cap_arg],
    );

    // agent as defined in the `cluster_tests.move`
    let agent_name_arg = ptb.pure(AGENT_NAME)?;
    let agent_role_arg = ptb.pure("AI Poet")?;
    let agent_goal_arg = ptb.pure("Create beautiful poems")?;
    let agent_backstory_arg =
        ptb.pure("An AI trained to create poetic masterpieces")?;

    ptb.programmable_move_call(
        ctx.pkg_id,
        Identifier::new(AGENT_MODULE)?,
        Identifier::new(AGENT_CREATE_AND_SHARE_FUNCTION)?,
        vec![],
        vec![
            agent_name_arg,
            agent_role_arg,
            agent_goal_arg,
            agent_backstory_arg,
            model_info_arg,
        ],
    );

    let events = ctx
        .execute_ptx(ptb.finish())
        .await?
        .events
        .ok_or_else(|| {
            anyhow!("No events found in the response of create agent ptx")
        })?
        .data;

    let Some(event_json) = events
        .into_iter()
        .find(|event| event.type_.name.to_string() == AGENT_CREATED_EVENT)
        .map(|event| event.parsed_json.clone())
    else {
        anyhow::bail!(
            "No {AGENT_CREATED_EVENT} found in \
            the response of create agent ptx"
        )
    };

    let agent_id_str = event_json["agent"].as_str().ok_or_else(|| {
        anyhow!("{AGENT_CREATED_EVENT}.agent is not a string")
    })?;
    let agent_owner_cap_id_str =
        event_json["owner_cap"].as_str().ok_or_else(|| {
            anyhow!("{AGENT_CREATED_EVENT}.owner_cap is not a string")
        })?;

    Ok(TestAgent {
        id: ObjectID::from_str(agent_id_str)?,
        owner_cap: ObjectID::from_str(agent_owner_cap_id_str)?,
    })
}

/// Sets up a new dummy cluster.
/// Returns cluster ID and cluster owner capability ID.
async fn create_cluster_with_owner_cap(
    ctx: &mut TestsContext,
) -> Result<TestCluster> {
    let events = ctx
        .move_call(
            CLUSTER_MODULE,
            CLUSTER_CREATE_FUNCTION,
            vec![
                // name: String
                SuiJsonValue::from_str_to_string("my-cluster-1")?,
                // description: String
                SuiJsonValue::from_str_to_string("Poet cluster")?,
            ],
        )
        .await?
        .events
        .ok_or_else(|| {
            anyhow!(
                "No events found in the response of create cluster transaction"
            )
        })?
        .data;

    let Some(event_json) = events
        .into_iter()
        .find(|event| event.type_.name.to_string() == CLUSTER_CREATED_EVENT)
        .map(|event| event.parsed_json.clone())
    else {
        anyhow::bail!(
            "No {CLUSTER_CREATED_EVENT} found in \
            the response of create cluster transaction"
        )
    };

    let cluster_id_str = event_json["cluster"].as_str().ok_or_else(|| {
        anyhow!("{CLUSTER_CREATED_EVENT}.cluster is not a string")
    })?;
    let cluster_owner_cap_id_str =
        event_json["owner_cap"].as_str().ok_or_else(|| {
            anyhow!("{CLUSTER_CREATED_EVENT}.owner_cap is not a string")
        })?;

    Ok(TestCluster {
        id: ObjectID::from_str(cluster_id_str)?,
        owner_cap: ObjectID::from_str(cluster_owner_cap_id_str)?,
    })
}

async fn add_agent_to_cluster(
    ctx: &mut TestsContext,
    agent: &TestAgent,
    cluster: &TestCluster,
) -> Result<()> {
    let cluster_ref = ctx.get_object_ref(cluster.id).await?;
    let cluster_owner_cap_ref = ctx.get_object_ref(cluster.owner_cap).await?;

    let agent_ref = ctx.get_object_ref(agent.id).await?;
    let agent_owner_cap_ref = ctx.get_object_ref(agent.owner_cap).await?;

    let mut ptb = ProgrammableTransactionBuilder::new();

    // talus::agent::get_blueprint(&Agent, &OwnerCap)
    let agent_arg = ptb.obj(ObjectArg::SharedObject {
        id: agent.id,
        initial_shared_version: agent_ref.1,
        mutable: false,
    })?;
    let agent_owner_cap_arg =
        ptb.obj(ObjectArg::ImmOrOwnedObject(agent_owner_cap_ref))?;
    let agent_blueprint_arg = ptb.programmable_move_call(
        ctx.pkg_id,
        Identifier::new(AGENT_MODULE)?,
        Identifier::new(AGENT_GET_BLUEPRINT_FUNCTION)?,
        vec![],
        vec![agent_arg, agent_owner_cap_arg],
    );

    // talus::cluster::add_agent(&mut Cluster, &OwnerCap, &AgentBlueprint)
    let cluster_arg = ptb.obj(ObjectArg::SharedObject {
        id: cluster.id,
        initial_shared_version: cluster_ref.1,
        mutable: true,
    })?;
    let cluster_owner_cap_arg =
        ptb.obj(ObjectArg::ImmOrOwnedObject(cluster_owner_cap_ref))?;
    ptb.programmable_move_call(
        ctx.pkg_id,
        Identifier::new(CLUSTER_MODULE)?,
        Identifier::new(CLUSTER_ADD_AGENT_FUNCTION)?,
        vec![],
        vec![cluster_arg, cluster_owner_cap_arg, agent_blueprint_arg],
    );

    ctx.execute_ptx(ptb.finish()).await?;

    Ok(())
}

#[derive(Default)]
struct TaskDefinition {
    task_name: &'static str,
    agent_name: &'static str,
    description: &'static str,
    expected_output: &'static str,
    prompt: &'static str,
    context: &'static str,
    tool: Option<ToolDefinition>,
}

#[derive(Default)]
struct ToolDefinition {
    tool_name: &'static str,
    args: &'static [&'static str],
}

async fn add_task_to_cluster(
    ctx: &mut TestsContext,
    cluster: &TestCluster,
    task: TaskDefinition,
) -> Result<()> {
    ctx.move_call(
        CLUSTER_MODULE,
        CLUSTER_ADD_TASK_ENTRY_FUNCTION,
        vec![
            // cluster: &mut Cluster
            SuiJsonValue::from_object_id(cluster.id),
            // owner_cap: &ClusterOwnerCap
            SuiJsonValue::from_object_id(cluster.owner_cap),
            // task_name: String
            SuiJsonValue::from_str_to_string(task.task_name)?,
            // agent_name: String
            SuiJsonValue::from_str_to_string(task.agent_name)?,
            // description: String
            SuiJsonValue::from_str_to_string(task.description)?,
            // expected_output: String
            SuiJsonValue::from_str_to_string(task.expected_output)?,
            // prompt: String
            SuiJsonValue::from_str_to_string(task.prompt)?,
            // context: String
            SuiJsonValue::from_str_to_string(task.context)?,
        ],
    )
    .await?;

    if let Some(ToolDefinition { tool_name, args }) = task.tool {
        info!("Attaching tool {tool_name} to task {}", task.task_name);
        ctx.move_call(
            CLUSTER_MODULE,
            CLUSTER_ATTACH_TASK_TOOL_FUNCTION,
            vec![
                // cluster: &mut Cluster
                SuiJsonValue::from_object_id(cluster.id),
                // owner_cap: &ClusterOwnerCap
                SuiJsonValue::from_object_id(cluster.owner_cap),
                // task_name: String
                SuiJsonValue::from_str_to_string(task.task_name)?,
                // tool_name: String
                SuiJsonValue::from_str_to_string(tool_name)?,
                // args: vector<String>
                SuiJsonValue::new(JsonValue::Array(
                    args.iter()
                        .map(ToOwned::to_owned)
                        .map(From::from)
                        .collect(),
                ))?,
            ],
        )
        .await?;
    }

    Ok(())
}
