#[test_only]
module talus::cluster_tests {
    use std::string;
    use sui::table;
    use sui::test_scenario::{Self, Scenario, ctx};
    use sui::test_utils::print;
    use talus::agent::{Self, AgentBlueprint, AgentName};
    use talus::cluster::{Self, Cluster, ClusterExecution, ClusterOwnerCap};
    use talus::model::{Self, ModelInfo};
    use talus::task::{Self, TaskBlueprint, TaskName};

    #[test]
    /// The goal of this test is to verify that a cluster can be set up and
    /// that two tasks can be executed successfully, proving that the state
    /// machine works.
    ///
    /// 1. We setup a cluster with two tasks: analyze poem request and create poem.
    /// 2. We simulate the execution of the cluster with a valid input and verify
    ///    that the cluster execution is in the correct state.
    /// 3. We simulate the completion of the first task (from the POV of an agent)
    ///    and verify that the cluster execution is in the correct state.
    /// 4. We simulate the completion of the second task (from the POV of an agent)
    ///    and verify that the cluster execution is successful.
    fun test_poem_creation_cluster() {
        let owner = @0x1;
        let mut scenario = test_scenario::begin(owner);

        //
        // 1.
        //
        setup_poem_creation_cluster(&mut scenario);

        //
        // 2.
        //
        test_scenario::next_tx(&mut scenario, owner);
        {
            print(b"Creating and executing cluster with valid input");
            let cluster = test_scenario::take_shared<Cluster>(&scenario);
            let input = string::utf8(b"Create a poem about nature in a romantic style");
            cluster::execute(&cluster, input, ctx(&mut scenario));
            test_scenario::return_shared(cluster);
        };
        test_scenario::next_tx(&mut scenario, owner);
        {
            let execution = test_scenario::take_shared<ClusterExecution>(&scenario);
            verify_initial_state(&execution);
            test_scenario::return_shared(execution);
        };

        //
        // 3.
        //
        test_scenario::next_tx(&mut scenario, owner);
        {
            let mut execution = test_scenario::take_shared<ClusterExecution>(&scenario);
            let owner_cap = test_scenario::take_from_address<ClusterOwnerCap>(&scenario, owner);
            let analysis_result = string::utf8(b"The user has requested a romantic poem about nature. Both style (romantic) and subject (nature) are present.");
            cluster::submit_completion_as_cluster_owner(&mut execution, &owner_cap, analysis_result);
            verify_analysis_state(&execution);
            test_scenario::return_shared(execution);
            test_scenario::return_to_address(owner, owner_cap);
        };

        //
        // 4.
        //
        test_scenario::next_tx(&mut scenario, owner);
        {
            let mut execution = test_scenario::take_shared<ClusterExecution>(&scenario);
            let owner_cap = test_scenario::take_from_address<ClusterOwnerCap>(&scenario, owner);
            let poem = string::utf8(b"Gentle breeze whispers through leaves,\nNature's love song in the air,\nMoonlit meadows, stars above,\nA romantic scene beyond compare.");
            cluster::submit_completion_as_cluster_owner(&mut execution, &owner_cap, poem);
            verify_final_state(&execution);
            test_scenario::return_shared(execution);
            test_scenario::return_to_address(owner, owner_cap);
        };

        test_scenario::end(scenario);
    }

    fun verify_initial_state(execution: &ClusterExecution) {
        assert!(cluster::is_execution_running(execution), 0);
        let tasks = cluster::get_execution_task_statuses(execution);
        assert!(table::length(tasks) == 2, 1);

        let task1 = table::borrow(tasks, task1_name());
        assert!(task::is_running(task1), 2);
        let task2 = table::borrow(tasks, task2_name());
        assert!(task::is_idle(task2), 3);
    }

    fun verify_analysis_state(execution: &ClusterExecution) {
        assert!(cluster::is_execution_running(execution), 0);
        let tasks = cluster::get_execution_task_statuses(execution);

        let task1 = table::borrow(tasks, task1_name());
        assert!(task::is_successful(task1), 1);
        let task2 = table::borrow(tasks, task2_name());
        assert!(task::is_running(task2), 2);
    }

    fun verify_final_state(execution: &ClusterExecution) {
        assert!(cluster::is_execution_successful(execution), 0);
        let tasks = cluster::get_execution_task_statuses(execution);

        let task1 = table::borrow(tasks, task1_name());
        assert!(task::is_successful(task1), 2);
        let task2 = table::borrow(tasks, task2_name());
        assert!(task::is_successful(task2) , 3);

        let response = cluster::get_execution_response(execution);
        assert!(string::index_of(&response, &string::utf8(b"Gentle breeze")) == 0, 4);
    }

    fun setup_poem_creation_cluster(scenario: &mut Scenario) {
        let ctx = ctx(scenario);

        let model = model::new_mock_info_for_testing(ctx);
        let manager_agent = create_manager_agent(&model);
        let poet_agent = create_poet_agent(&model);
        let poet_agent_name = agent::get_name(&poet_agent);

        let task1 = create_task1(poet_agent_name);
        let task2 = create_task2(poet_agent_name);

        cluster::create(
            string::utf8(b"Poem Creation Cluster"),
            string::utf8(b"A cluster for creating custom poems"),
            ctx
        );

        test_scenario::next_tx(scenario, @0x1);
        {
            let mut cluster = test_scenario::take_shared<Cluster>(scenario);
            let cap = test_scenario::take_from_address<ClusterOwnerCap>(scenario, @0x1);
            cluster::add_agent(&mut cluster, &cap, manager_agent);
            cluster::add_agent(&mut cluster, &cap, poet_agent);
            cluster::add_task(&mut cluster, &cap, task1);
            cluster::add_task(&mut cluster, &cap, task2);
            test_scenario::return_shared(cluster);
            test_scenario::return_to_address(@0x1, cap);
        };
    }

    fun create_manager_agent(model: &ModelInfo): AgentBlueprint {
        agent::new(
            agent::into_name(string::utf8(b"Manager")),
            string::utf8(b"Poem Creation Manager"),
            string::utf8(b"Manage the poem creation process"),
            string::utf8(b"An AI trained to oversee poem creation"),
            *model,
        )
    }

    fun create_poet_agent(model: &ModelInfo): AgentBlueprint {
        agent::new(
            agent::into_name(string::utf8(b"Poet")),
            string::utf8(b"AI Poet"),
            string::utf8(b"Create beautiful poems"),
            string::utf8(b"An AI trained to create poetic masterpieces"),
            *model,
        )
    }

    fun task1_name(): TaskName {
        task::into_name(string::utf8(b"Analyze Poem Request"))
    }

    fun create_task1(agent: AgentName): TaskBlueprint {
        task::new(
            task1_name(),
            agent,
            string::utf8(b"Analyze the user's request for poem creation"),
            string::utf8(b"A structured analysis of the poem request"),
            string::utf8(b"Analyze the user's input for poem style and subject. If either is missing, prepare an error message."),
            string::utf8(b""),
        )
    }

    fun task2_name(): TaskName {
        task::into_name(string::utf8(b"Create Poem"))
    }

    fun create_task2(agent: AgentName): TaskBlueprint {
        task::new(
            task2_name(),
            agent,
            string::utf8(b"Create a poem based on the analyzed request"),
            string::utf8(b"A poem matching the user's requirements"),
            string::utf8(b"Create a poem based on the provided style and subject. Be creative and inspiring."),
            string::utf8(b""),
        )
    }
}
