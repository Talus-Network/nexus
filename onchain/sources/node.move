module talus::node {
    //! A [`Node`] is a computational unit that can run one or more models.
    //!
    //! From a node we create models.
    //! From a model we create agents.
    //! From agents we create a clusters.

    use std::string::String;
    use sui::event;
    use sui::transfer::transfer;

    // === Data models ===

    /// Meant as an owned object.
    /// By having ownership of this object you can create new models that are
    /// bound to this node.
    ///
    /// TODO: In future this should have the same ownership pattern as models
    ///       and agents.
    public struct Node has key, store {
        id: UID,
        name: String,
        node_type: String,
        gpu_memory: u64,
        image_hash: vector<u8>,
        external_arguments: vector<u8>,
    }

    // === Events ===

    public struct NodeCreatedEvent has copy, drop {
        node: ID,
        name: String,
    }

    // === Constructors ===

    public entry fun create(
        name: String,
        node_type: String,
        gpu_memory: u64,
        image_hash: vector<u8>,
        external_arguments: vector<u8>,
        ctx: &mut TxContext,
    ) {
        let node = Node {
            id: object::new(ctx),
            name,
            node_type,
            gpu_memory,
            image_hash,
            external_arguments,
        };

        event::emit(NodeCreatedEvent {
            node: object::id(&node),
            name: node.name,
        });

        transfer(node, ctx.sender());
    }
}
