module talus::agent {
    //! An agent is a specialized entity designed to perform specific roles
    //! within the [`talus::Cluster::Cluster`] setup.
    //!
    //! From a node we create models.
    //! From a model we create agents.
    //! From agents we create a clusters.
    //!
    //! There are two ways of going about creating an agent:
    //! 1. Cluster owner can create a blueprint directly and add that blueprint to their cluster.
    //!    Useful if the cluster owner runs the agent's inference node off-chain.
    //! 2. A model provider can create a shared [`Agent`] object and let other clusters use it.
    //!
    //! # Using a shared agent
    //! A cluster owner can add an agent to the cluster setup by redeeming a [`AgentRosterPromise`].
    //! This object can be created by the agent owner.
    //! It can be sent to the cluster owner, or it can be sold to them as an NFT.

    use std::string::{Self, String};
    use sui::event;
    use sui::transfer::{transfer, share_object};
    use talus::model::ModelInfo;

    // === Errors ===

    const EAgentMismatch: u64 = 1;
    const ENotAgentOwner: u64 = 2;

    // === Data models ===

    /// Other clusters can copy [`AgentBlueprint`] from this object to include this
    /// agent in their setup.
    /// They need the corresponding [`AgentRosterPromise`] to do that.
    public struct Agent has key, store {
        id: UID,
        /// We mustn't give references the blueprint because at the moment having
        /// access to [`AgentBlueprint`] means being able to request completions
        /// from the agent owner.
        blueprint: AgentBlueprint,
    }

    /// When [`Agent`] is created, the sender of the transaction becomes the owner.
    /// This is typically an owned object.
    /// The owner of this object can submit transactions with the agent's completions.
    ///
    /// The cap can be cloned with [`clone_owner_cap`].
    /// This is useful if the agent owner runs multiple machines but wants to
    /// keep their private keys separate, or if they want to emit [`AgentRosterPromise`]
    /// from a Move package.
    public struct AgentOwnerCap has key, store {
        id: UID,
        agent: ID,
    }

    /// Defines the kind of work this agent typically does.
    /// If the agent is an LLM, some of this information will be used for
    /// pre-prompt.
    ///
    /// TBD: If we allow mutation of this data, we also need to add a version.
    public struct AgentBlueprint has store, copy, drop {
        /// Agents are identified by their name.
        /// This implies that agent name must be unique within single [`talus::cluster::Cluster`].
        name: AgentName,
        /// If this blueprint was created from another agent, this field will
        /// contain the ID of the originating agent.
        ///
        /// If this blueprint was created by a cluster owner without referencing
        /// existing agent, then this field will be `None`.
        ///
        /// This decides who can submit completions on behalf of the agent.
        originated_from_agent: Option<ID>,
        /// We must't give references to the model because at the moment having
        /// access to [`ModelInfo`] means being able to request completions
        /// from the model owner.
        /// But model owner must have a say over who can request completions.
        model: ModelInfo,
        role: String,
        goal: String,
        backstory: String,
    }

    /// Agent's state specific to [`talus::cluster::ClusterExecution`].
    /// Our first implementation is sequential execution, we don't support
    /// hierarchy of agents yet.
    /// Therefore, no agent is a manager.
    public struct AgentState has store {
        name: AgentName,
        last_task_response: String,
    }

    /// Agent name serves as an identifier for an agent.
    public struct AgentName has store, copy, drop {
        inner: String,
    }

    /// A cluster owner can exchange this object for an agent in their setup.
    /// The owner of an agent promises to submit completions on behalf of the
    /// agent when the agent is added to the cluster.
    ///
    /// This object can be treated as an NFT.
    public struct AgentRosterPromise has key, store {
        id: UID,
        agent: ID,
    }

    // === Events ===

    public struct AgentCreatedEvent has copy, drop {
        agent: ID,
        owner_cap: ID,
    }

    public struct AgentRosterPromiseIssuedEvent has copy, drop {
        promise: ID,
        agent: ID,
    }

    // === Constructors ===

    /// Returns a new instance of an [`AgentBlueprint`].
    /// The blueprint is not associated with any specific agent and it's up to
    /// the caller to ensure that there are off-chain services that can run the
    /// agent.
    ///
    /// Does NOT emit any event.
    public fun new(
        name: AgentName,
        role: String,
        goal: String,
        backstory: String,
        model: ModelInfo,
    ): AgentBlueprint {
        AgentBlueprint {
            name,
            role,
            goal,
            backstory,
            model,
            originated_from_agent: option::none(),
        }
    }

    /// Creates a new [`Agent`] from blueprint.
    /// Typically, the [`AgentOwnerCap`] is transferred as an owned object to
    /// the agent owner and the [`Agent`] is shared.
    public fun create_from_blueprint(
        blueprint: AgentBlueprint,
        ctx: &mut TxContext,
    ): (AgentOwnerCap, Agent) {
        let agent = Agent {
            id: object::new(ctx),
            blueprint,
        };

        let owner_cap = AgentOwnerCap {
            id: object::new(ctx),
            agent: object::id(&agent),
        };

        event::emit(AgentCreatedEvent {
            agent: object::id(&agent),
            owner_cap: object::id(&owner_cap),
        });

        (owner_cap, agent)
    }

    #[allow(lint(share_owned, self_transfer))]
    /// Similar to [`create_from_blueprint`] but tailored towards calls from
    /// programmable txs.
    /// The [`AgentOwnerCap`] is transferred to the tx sender as an owned object
    /// and [`Agent`] is shared.
    public fun create_and_share(
        name: String, // AgentName as string for convenience
        role: String,
        goal: String,
        backstory: String,
        model: ModelInfo,
        ctx: &mut TxContext,
    ) {
        let blueprint = new(
            into_name(name),
            role,
            goal,
            backstory,
            model,
        );

        let (owner_cap, agent) = create_from_blueprint(blueprint, ctx);

        transfer(owner_cap, ctx.sender());
        share_object(agent);
    }

    /// The agent's owner can issue a promise to any cluster owner that ends up
    /// owning the [`AgentRosterPromise`] that the agent will participate in
    /// their cluster.
    public fun issue_roster_promise(
        owner_cap: &AgentOwnerCap, ctx: &mut TxContext,
    ): AgentRosterPromise {
        let promise = AgentRosterPromise {
            id: object::new(ctx),
            agent: owner_cap.agent,
        };

        event::emit(AgentRosterPromiseIssuedEvent {
            promise: object::id(&promise),
            agent: owner_cap.agent,
        });

        promise
    }

    /// Create a new instance of a [`AgentName`] from given string.
    /// Name serves as an identifier.
    public fun into_name(s: String): AgentName {
        AgentName { inner: s }
    }

    /// Creates another owner cap for the same agent.
    public fun clone_owner_cap(
        self: &AgentOwnerCap, ctx: &mut TxContext,
    ): AgentOwnerCap {
        AgentOwnerCap {
            id: object::new(ctx),
            agent: self.agent,
        }
    }

    /// Returns new empty state for the agent.
    public fun new_state(agent_name: AgentName): AgentState {
        AgentState {
            name: agent_name,
            last_task_response: string::utf8(b""),
        }
    }

    // === Destructors ===

    public fun destroy_owner_cap(self: AgentOwnerCap) {
        let AgentOwnerCap { id, .. } = self;
        object::delete(id);
    }

    // === Package protected ===

    /// Returns a blueprint for the agent.
    /// When the agent is added to the cluster we emit an event that notifies the
    /// agent's owner.
    public(package) fun redeem_roster_promise(
        agent: &Agent,
        promise: AgentRosterPromise,
    ): AgentBlueprint {
        assert!(object::id(agent) == promise.agent, EAgentMismatch);

        let mut blueprint = agent.blueprint;
        blueprint.originated_from_agent = option::some(object::id(agent));

        let AgentRosterPromise { id, .. } = promise;
        id.delete();

        blueprint
    }

    // === Accessors ===

    /// Only the owner can get the blueprint on chain as this is what we create
    /// clusters from.
    public fun get_blueprint(
        self: &Agent, owner_cap: &AgentOwnerCap,
    ): AgentBlueprint {
        assert_owner(self, owner_cap);
        let mut blueprint = self.blueprint;
        blueprint.originated_from_agent = option::some(object::id(self));

        blueprint
    }

    public fun get_backstory(self: &AgentBlueprint): String { self.backstory }
    public fun get_goal(self: &AgentBlueprint): String { self.goal }
    public fun get_model_id(self: &AgentBlueprint): ID { self.model.get_id() }
    public fun get_name(self: &AgentBlueprint): AgentName { self.name }
    public fun get_node_id(self: &AgentBlueprint): ID { self.model.get_node_id() }
    public fun get_originated_from_agent(self: &AgentBlueprint): Option<ID> { self.originated_from_agent }
    public fun get_role(self: &AgentBlueprint): String { self.role }

    public fun get_owner_cap_agent(self: &AgentOwnerCap): ID { self.agent }

    public fun get_roster_promised_agent(self: &AgentRosterPromise): ID { self.agent }

    // === Package protected ===

    /// See AgentBlueprint.model for why this is package protected.
    public(package) fun get_model_info(self: &AgentBlueprint): ModelInfo { self.model }

    public(package) fun set_last_task_response(self: &mut AgentState, response: String) {
        self.last_task_response = response;
    }

    // === Helpers ===

    fun assert_owner(agent: &Agent, owner_cap: &AgentOwnerCap) {
        assert!(owner_cap.agent == object::id(agent), ENotAgentOwner);
    }
}
