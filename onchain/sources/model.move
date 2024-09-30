module talus::model {
    //! Models represent software that runs on a [`Node`].
    //! The on-chain definition is descriptive so that agent owners and cluster
    //! owners have exact idea of what will power their apps.
    //!
    //! From a node we create models.
    //! From a model we create agents.
    //! From agents we create a clusters.

    use std::string::String;
    use sui::event;
    use sui::transfer::{share_object, transfer};
    use talus::node::Node;

    #[test_only]
    use std::string::utf8;

    // === Errors ===

    const EModelHashCannotBeEmpty: u64 = 1;
    const EModelMismatch: u64 = 2;
    const ENotModelOwner: u64 = 3;

    // === Data models ===

    /// Shared object that is used to create agents.
    ///
    /// TBD: Discuss how can we pause or disable a model gracefully.
    ///      The problem is that we copy model information to agents and from
    ///      agents to clusters. This complicates updates. Especially it
    ///      complicates the pausing/resuming, because we have to pause an agent
    ///      and therefore all clusters that use it.
    public struct Model has key, store {
        id: UID,
        info: ModelInfo,
    }

    /// Allows updating of the model, halting and resuming it and can issue
    /// an inference promise for agents.
    public struct ModelOwnerCap has key, store {
        id: UID,
        model: ID,
    }

    /// Model parameters that define what software is running on a [`Node`].
    public struct ModelInfo has store, drop, copy {
        /// The ID of the [`Model`] that is associated with this info.
        id: ID,
        /// The ID of the [`Node`] that runs this model.
        node: ID,
        capacity: u64,
        datasets: vector<String>,
        description: String,
        family: String,
        is_fine_tuned: bool,
        is_open_source: bool,
        max_context_length: u64,
        model_hash: vector<u8>,
        name: String,
        num_params: u64,
        token_price: u64,
        url: String,
        vendor: String,
    }

    /// A model owner can issue an inference promise that can be used to create
    /// agents.
    /// Since right now we don't have a way to punish model owners for not
    /// delivering the promised inference, as of this version of the protocol
    /// this is a "promise".
    ///
    /// The model owner uses this object to manage how many agents can be
    /// created from this model.
    ///
    /// This object can be treated as an NFT.
    public struct ModelInferencePromise has key, store {
        id: UID,
        model: ID,
    }

    // === Events ===

    public struct ModelCreatedEvent has copy, drop {
        by: address,
        model: ID,
        name: String,
        node: ID,
        owner_cap: ID,
    }

    public struct ModelInferencePromiseIssuedEvent has copy, drop {
        model: ID,
        promise: ID,
    }

    // === Constructors ===

    /// Creates a new shared [`Model`] object.
    public entry fun create(
        node: &Node,
        name: String,
        model_hash: vector<u8>,
        url: String,
        token_price: u64,
        capacity: u64,
        num_params: u64,
        description: String,
        max_context_length: u64,
        is_fine_tuned: bool,
        family: String,
        vendor: String,
        is_open_source: bool,
        datasets: vector<String>,
        ctx: &mut TxContext,
    ) {
        assert!(!vector::is_empty(&model_hash), EModelHashCannotBeEmpty);

        let model_uid = object::new(ctx);

        let info = ModelInfo {
            id: object::uid_to_inner(&model_uid),
            name,
            model_hash,
            node: object::id(node),
            url,
            token_price,
            capacity,
            num_params,
            description,
            max_context_length,
            is_fine_tuned,
            family,
            vendor,
            is_open_source,
            datasets,
        };

        let model = Model {
            id: model_uid,
            info,
        };

        let owner_cap = ModelOwnerCap {
            id: object::new(ctx),
            model: object::id(&model),
        };

        event::emit(ModelCreatedEvent {
            by: ctx.sender(),
            model: object::id(&model),
            name: info.name,
            node: info.node,
            owner_cap: object::id(&owner_cap),
        });

        transfer(owner_cap, ctx.sender());
        share_object(model);
    }

    /// Whoever holds this object can create agents.
    public fun issue_inference_promise(
        owner_cap: &ModelOwnerCap, ctx: &mut TxContext,
    ): ModelInferencePromise {
        let promise = ModelInferencePromise {
            id: object::new(ctx),
            model: owner_cap.model,
        };

        event::emit(ModelInferencePromiseIssuedEvent {
            model: owner_cap.model,
            promise: object::id(&promise),
        });

        promise
    }

    /// Creates another owner cap for the same model.
    public fun clone_owner_cap(
        owner_cap: &ModelOwnerCap, ctx: &mut TxContext,
    ): ModelOwnerCap {
        ModelOwnerCap {
            id: object::new(ctx),
            model: owner_cap.model,
        }
    }

    /// We can create agents with the [`ModelInfo`] object.
    public fun redeem_inference_promise(
        model: &Model,
        promise: ModelInferencePromise,
    ): ModelInfo {
        assert!(object::id(model) == promise.model, EModelMismatch);

        let ModelInferencePromise { id, .. } = promise;
        object::delete(id);

        model.info
    }

    // === Destructors ===

    public fun destroy_owner_cap(self: ModelOwnerCap) {
        let ModelOwnerCap { id, .. } = self;
        object::delete(id);
    }

    // === Accessors ===

    /// Only the owner can get the info on chain as this is what we create
    /// agents from.
    public fun get_info(self: &Model, owner_cap: &ModelOwnerCap): ModelInfo {
        assert_owner(self, owner_cap);
        self.info
    }

    public fun get_name(self: &ModelInfo): String { self.name }
    public fun get_id(self: &ModelInfo): ID { self.id }
    public fun get_node_id(self: &ModelInfo): ID { self.node }

    public fun get_model_id(self: &ModelOwnerCap): ID { self.model }

    // === Helpers ===

    fun assert_owner(model: &Model, owner_cap: &ModelOwnerCap) {
        assert!(owner_cap.model == object::id(model), ENotModelOwner);
    }

    // === Tests ===

    #[test_only]
    public fun new_info_for_testing(
        id: ID,
        name: String,
        model_hash: vector<u8>,
        node: ID,
        url: String,
        token_price: u64,
        capacity: u64,
        num_params: u64,
        description: String,
        max_context_length: u64,
        is_fine_tuned: bool,
        family: String,
        vendor: String,
        is_open_source: bool,
        datasets: vector<String>,
    ): ModelInfo {
        ModelInfo {
            id,
            name,
            model_hash,
            node,
            url,
            token_price,
            capacity,
            num_params,
            description,
            max_context_length,
            is_fine_tuned,
            family,
            vendor,
            is_open_source,
            datasets,
        }
    }

    #[test_only]
    /// Creates a new [`ModelInfo`] object with mock data
    public fun new_mock_info_for_testing(ctx: &mut TxContext): ModelInfo {
        let mock_node_uid = object::new(ctx);
        let mock_node_id = object::uid_to_inner(&mock_node_uid);
        object::delete(mock_node_uid);

        let mock_model_uid = object::new(ctx);
        let mock_model_id = object::uid_to_inner(&mock_model_uid);
        object::delete(mock_model_uid);

        new_info_for_testing(
            mock_model_id,
            utf8(b"Test Model"),
            b"model_hash",
            mock_node_id,
            utf8(b"http://example.com"),
            100,
            1000,
            1000000,
            utf8(b"Test Description"),
            16,
            false,
            utf8(b"Test Family"),
            utf8(b"Test Vendor"),
            false,
            vector::empty(),
        )
    }
}
