#[test_only]
module talus::node_tests {
    use sui::test_scenario;
    use talus::node::{Self, Node};
    use std::string;

    #[test]
    fun test_create_node() {
        let mut scenario = test_scenario::begin(@0x1);
        let ctx = test_scenario::ctx(&mut scenario);

        // Create a node
        node::create(
            string::utf8(b"Test Node"),
            string::utf8(b"GPU"),
            16,
            vector::empty(),
            vector::empty(),
            ctx
        );

        // Move to the next transaction
        test_scenario::next_tx(&mut scenario, @0x1);

        // Check if the node was created and owned
        assert!(test_scenario::has_most_recent_for_sender<Node>(&scenario), 0);

        // Get the created node
        let node = test_scenario::take_from_sender<Node>(&scenario);

        // Return the node to the scenario
        test_scenario::return_to_sender(&scenario, node);

        test_scenario::end(scenario);
    }
}
