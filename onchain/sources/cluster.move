module talus::cluster {
    //! A [`Cluster`] is a group of agents working together to achieve a common goal.
    //! A concrete goal they are working towards is called [`ClusterExecution`].
    //!
    //! First, a new [`Cluster`] is created with a blueprint of agents and tasks.
    //! Then whenever a user submits new prompt, a new [`ClusterExecution`] is created
    //! and the current version of the blueprint is copied.
    //! The off-chain services then work towards the completion of the goal.
    //!
    //! From a node we create models.
    //! From a model we create agents.
    //! From agents we create a clusters.

    use std::hash;
    use std::string::{Self, String, utf8};
    use sui::event;
    use sui::table_vec::{Self, TableVec};
    use sui::table::{Self, Table};
    use sui::vec_map::{Self, VecMap};
    use talus::agent::{Self, AgentName, AgentBlueprint, AgentState, Agent, AgentRosterPromise};
    use talus::consts::{status_idle, status_running, status_success};
    use talus::model::{Self, ModelOwnerCap, Model};
    use talus::node::Node;
    use talus::tool;
    use talus::prompt;
    use talus::task::{Self, TaskName, TaskState, TaskBlueprint};

    // === Errors ===

    const ENoTasksToExecute: u64 = 1;
    const ECurrentTaskNotIdle: u64 = 2;
    const ETaskNotFound: u64 = 3;
    const ENotClusterOwner: u64 = 4;
    const ENodeMismatch: u64 = 5;
    const EModelMismatch: u64 = 6;

    // === Consts ===

    /// For the first iteration of Nexus, we arbitrarily chose to include this
    /// many latest messages in the context for the next prompt.
    const PastNMessagesToIncludeInContext: u64 = 5;

    // === Data models ===

    /// An object that holds a cluster definition.
    public struct Cluster has key, store {
        id: UID,
        blueprint: ClusterBlueprint,
    }

    /// Usually an owned object that permissions operations on the [`Cluster`].
    ///
    /// The cap can be cloned with [`clone_owner_cap`].
    /// This is useful if the cluster owner runs multiple machines but wants to
    /// keep their private keys separate.
    public struct ClusterOwnerCap has key, store {
        id: UID,
        cluster: ID,
    }

    /// Blueprint for execution.
    ///
    /// TBD: We use [`VecMap`] for agents.
    ///     This allows trivial copies of the data.
    ///     However, we would preferably use [`Table`] instead and referenced
    ///     the agents by their name in the [`ClusterExecution`].
    ///     We need to first figure out a good strategy for versioning to enable
    ///     editing of Cluster blueprints.
    ///     [`VecMap`] is a good in between step towards that goal.
    ///     As for tasks, those need to be ordered.
    ///     The same scenario applies to tasks, except we want [`TableVec`]
    /// TBD: We should keep a version in the blueprint struct and bump it on
    ///      every update.
    public struct ClusterBlueprint has store, copy, drop {
        name: String,
        description: String,
        tasks: vector<TaskBlueprint>,
        agents: VecMap<AgentName, AgentBlueprint>,
    }

    // This is what the user is paying for
    public struct ClusterExecution has key, store {
        id: UID,
        from_cluster: ID,
        blueprint: ClusterBlueprint,
        running_user: address,
        created_at_epoch: u64,
        tasks: Table<TaskName, TaskState>,
        agents: Table<AgentName, AgentState>,
        /// With what prompt was the execution started.
        cluster_user_message: String,
        /// The final response of the cluster execution.
        /// Empty until status is `StatusSuccess`.
        cluster_response: String,
        current_task: TaskName,
        /// Enumeration of
        /// - `StatusIdle`
        /// - `StatusRunning`
        /// - `StatusSuccess`
        ///
        /// We use string constants to be more friendly to explorers.
        /// See [`talus::consts`].
        status: String,
        memory: Memory,
    }

    /// Right now memory consists of past messages.
    /// We simply use past [`PastNMessagesToIncludeInContext`] message to build
    /// the context for next prompt execution.
    public struct Memory has store {
        messages: TableVec<Message>,
    }

    public struct Message has store, drop {
        role: String,
        content: String,
        name: Option<String>,
    }

    // === Events ===

    /// A new [`Cluster`] has been created.
    /// It can be populated with agents and tasks later.
    public struct ClusterCreatedEvent has copy, drop {
        cluster: ID,
        owner_cap: ID,
    }

    /// A new [`ClusterExecution`] has been created.
    public struct ClusterExecutionCreatedEvent has copy, drop {
        cluster: ID,
        execution: ID,
    }

    public struct ClusterResponseEvent has copy, drop {
        cluster: ID,
        cluster_name: String,
        // should not be a string in order to be able to support
        // different types of responses images music etc.
        // TBD: Do we really want to store the response in the event? With large
        // responses this will be expensive.
        response: vector<u8>,
    }

    public struct AgentAddedToClusterEvent has copy, drop {
        cluster: ID,
        agent_name: AgentName,
        /// Only present if the agent's blueprint was copied from existing agent
        /// and not created from scratch.
        /// See [`talus::agent::redeem_roster_promise`].
        ///
        /// The agent's owner can the filter this event by this value to know
        /// which of their agents were added to a cluster.
        agent: Option<ID>,
        /// Which model is the agent using.
        model: ID,
        /// On which HW is the agent running.
        node: ID,
    }

    // === Constructors ===

    /// Create an empty [`Cluster`] shared object.
    /// The tx sender gets an owned object [`ClusterOwnerCap`] that allows them to
    /// modify the cluster.
    public entry fun create(
        name: String,
        description: String,
        ctx: &mut TxContext
    ) {
        let cluster = Cluster {
            id: object::new(ctx),
            blueprint: ClusterBlueprint {
                name,
                description,
                agents: vec_map::empty(),
                tasks: vector::empty(),
            }
        };

        let owner_cap = ClusterOwnerCap {
            id: object::new(ctx),
            cluster: object::id(&cluster),
        };

        event::emit(ClusterCreatedEvent {
            cluster: object::id(&cluster),
            owner_cap: object::id(&owner_cap),
        });

        transfer::share_object(cluster);
        transfer::transfer(owner_cap, ctx.sender());
    }

    /// Creates another owner cap for the same cluster.
    public fun clone_owner_cap(
        self: &ClusterOwnerCap, ctx: &mut TxContext,
    ): ClusterOwnerCap {
        ClusterOwnerCap {
            id: object::new(ctx),
            cluster: self.cluster,
        }
    }

    /// From given cluster blueprint, create a new [`ClusterExecution`] shared object.
    public entry fun execute(
        cluster: &Cluster,
        user_input: String,
        ctx: &mut TxContext,
    ) {
        if (cluster.blueprint.tasks.is_empty() ) {
            // The cluster was not yet configured to perform any tasks.
            std::debug::print(&utf8(b"No tasks to execute"));
            abort ENoTasksToExecute
        };

        // Populate tasks
        let mut task_states = table::new<TaskName, TaskState>(ctx);
        let mut i = 0;
        while (i < cluster.blueprint.tasks.length()) {
            let task = cluster.blueprint.tasks.borrow(i);
            let task_name = task.get_name();
            table::add(
                &mut task_states,
                task_name,
                task::new_state(task_name, task.get_agent_name()),
            );

            i = i + 1;
        };


        // Populate agents
        let mut agent_states = table::new<AgentName, AgentState>(ctx);
        let agent_names = cluster.blueprint.agents.keys();
        let mut i = 0;
        while (i < agent_names.length()) {
            let agent_name = *agent_names.borrow(i);
            table::add(
                &mut agent_states,
                agent_name,
                agent::new_state(agent_name),
            );

            i = i + 1;
        };

        let mut execution = ClusterExecution {
            id: object::new(ctx),
            from_cluster: object::id(cluster),
            blueprint: cluster.blueprint,
            running_user: ctx.sender(),
            created_at_epoch: ctx.epoch(),
            cluster_user_message: user_input,
            tasks: task_states,
            agents: agent_states,
            cluster_response: string::utf8(b""),
            // we already checked earlier that there are tasks in the blueprint
            current_task: task::get_name(cluster.blueprint.tasks.borrow(0)),
            status: status_idle(),
            memory: Memory {
                messages: table_vec::empty(ctx),
            },
        };

        // Add initial user message to memory
        add_message(
            &mut execution.memory,
            string::utf8(b"user"),
            user_input,
            option::none(),
        );

        // we already checked earlier that there are tasks in the blueprint
        schedule_current_task_for_execution(&mut execution);

        event::emit(ClusterExecutionCreatedEvent {
            cluster: object::id(cluster),
            execution: object::id(&execution),
        });

        transfer::share_object(execution)
    }

    // === State management ===

    /// Each agent's model has a node ID associated with it.
    /// This entry function allows the node owner to submit the completion of
    /// the prompt to the chain.
    public entry fun submit_completion_as_node_owner(
        execution: &mut ClusterExecution,
        node: &Node,
        completion: String,
    ) {
        let current_task_state = execution.tasks.borrow_mut(
            execution.current_task,
        );
        let agent_name = current_task_state.get_state_agent_name();
        let agent = execution.blueprint.agents.get(&agent_name);
        assert!(agent.get_node_id() == object::id(node), ENodeMismatch);

        submit_completion(execution, completion);
    }

    /// Each agent has a model ID associated with it.
    /// This entry function allows the model owner to submit the completion of
    /// the prompt to the chain.
    public entry fun submit_completion_as_model_owner(
        execution: &mut ClusterExecution,
        owner_cap: &ModelOwnerCap,
        completion: String,
    ) {
        let current_task_state = execution.tasks.borrow_mut(
            execution.current_task,
        );
        let agent_name = current_task_state.get_state_agent_name();
        let agent = execution.blueprint.agents.get(&agent_name);
        assert!(agent.get_model_id() == owner_cap.get_model_id(), EModelMismatch);

        submit_completion(execution, completion);
    }

    /// Cluster owner can submit completion on behalf of any agent.
    public entry fun submit_completion_as_cluster_owner(
        execution: &mut ClusterExecution,
        owner_cap: &ClusterOwnerCap,
        completion: String,
    ) {
        execution.assert_execution_owner(owner_cap);
        submit_completion(execution, completion);
    }

    /// Exchanges a roster promise for an agent blueprint and adds it to the cluster.
    public entry fun redeem_roster_promise(
        cluster: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        agent: &Agent,
        roster_promise: AgentRosterPromise,
    ) {
        let blueprint = agent.redeem_roster_promise(roster_promise);

        // SAFETY: checks for permissions in the function
        cluster.add_agent(owner_cap, blueprint);
    }

    public fun add_agent(
        self: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        agent: AgentBlueprint,
    ) {
        self.assert_owner(owner_cap);

        event::emit(AgentAddedToClusterEvent {
            cluster: object::id(self),
            agent_name: agent.get_name(),
            agent: agent.get_originated_from_agent(),
            model: agent.get_model_id(),
            node: agent.get_node_id(),
        });

        self.blueprint.agents.insert(agent.get_name(), agent);
    }

    public entry fun add_agent_entry(
        self: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        model: &Model,
        model_owner_cap: &ModelOwnerCap,
        agent_name: String,
        role: String,
        goal: String,
        backstory: String,
    ) {
        let agent_name_obj = agent::into_name(agent_name);
        let model_info = model::get_info(model, model_owner_cap);
        let agent = agent::new(agent_name_obj, role, goal, backstory, model_info);

        add_agent(self, owner_cap, agent);
    }

    public fun add_task(
        self: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        task: TaskBlueprint,
    ) {
        self.assert_owner(owner_cap);

        self.blueprint.tasks.push_back(task);
    }

    /// Adds a task to the cluster tailored for off-chain clients.
    public entry fun add_task_entry(
        cluster: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        task_name: String, // converted to TaskName
        agent_name: String, // converted to AgentName
        description: String,
        expected_output: String,
        prompt: String,
        context: String,
    ) {
        let task = task::new(
            task::into_name(task_name),
            agent::into_name(agent_name),
            description,
            expected_output,
            prompt,
            context,
        );

        // SAFETY: checks for permissions in the function
        add_task(cluster, owner_cap, task);
    }

    /// When using [add_task_entry] we create a task without a tool.
    /// One can attach a tool to a task using this function.
    /// You must ensure that the agent will know about this tool and
    /// how to use it.
    /// This will be improved upon in second iteration.
    public entry fun attach_tool_to_task_entry(
        cluster: &mut Cluster,
        owner_cap: &ClusterOwnerCap,
        task_name: String,
        tool_name: String,
        args: vector<String>,
    ) {
        cluster.assert_owner(owner_cap);

        let (_, task) = find_task_mut(
            &mut cluster.blueprint, task::into_name(task_name),
        );
        task.attach_tool(tool::new(tool_name, args));
    }

    // === Destructors ===

    public fun destroy_owner_cap(self: ClusterOwnerCap) {
        let ClusterOwnerCap { id, .. } = self;
        object::delete(id);
    }

    // === Accessors ===

    public fun get_cluster_blueprint(self: &Cluster): &ClusterBlueprint { &self.blueprint }
    public fun get_execution_blueprint(self: &ClusterExecution): &ClusterBlueprint { &self.blueprint }
    public fun get_execution_response_bytes(self: &ClusterExecution): vector<u8> { *string::bytes(&self.cluster_response) }
    public fun get_execution_response(self: &ClusterExecution): String { self.cluster_response }
    public fun get_execution_status(self: &ClusterExecution): String { self.status }
    public fun get_execution_task_statuses(self: &ClusterExecution): &Table<TaskName, TaskState> { &self.tasks }
    public fun get_tasks(self: &ClusterBlueprint): &vector<TaskBlueprint> { &self.tasks }
    public fun is_execution_idle(self: &ClusterExecution): bool { self.status == status_idle() }
    public fun is_execution_running(self: &ClusterExecution): bool { self.status == status_running() }
    public fun is_execution_successful(self: &ClusterExecution): bool { self.status == status_success() }

    // === Helpers ===

    fun assert_owner(self: &Cluster, owner_cap: &ClusterOwnerCap) {
        assert!(owner_cap.cluster == object::id(self), ENotClusterOwner);
    }

    fun assert_execution_owner(self: &ClusterExecution, owner_cap: &ClusterOwnerCap) {
        assert!(owner_cap.cluster == self.from_cluster, ENotClusterOwner);
    }

    /// An off-chain node that runs the inference submits the completion of the
    /// prompt to the chain.
    ///
    /// Before calling this function, the caller must verify that the tx sender
    /// is permitted to submit the completion on the current agent's behalf.
    fun submit_completion(
        execution: &mut ClusterExecution,
        completion: String,
    ) {
        // update task state to success and store the completion
        let current_task_state = execution.tasks.borrow_mut(
            execution.current_task,
        );
        current_task_state.set_state_status(status_success());
        current_task_state.set_state_response(completion);

        // update the agent's last task response
        let agent_state = execution.agents.borrow_mut(
            current_task_state.get_state_agent_name(),
        );
        agent_state.set_last_task_response(completion);

        add_message(
            &mut execution.memory,
            string::utf8(b"assistant"),
            completion,
            option::none(),
        );

        // find the next task
        let (current_task_index, _) = current_task(execution);
        let next_task_index = current_task_index + 1;

        if (next_task_index < execution.blueprint.tasks.length()) {
            let next_task = execution.blueprint.tasks.borrow(next_task_index);
            execution.current_task = next_task.get_name();
            execution.status = status_running();
            schedule_current_task_for_execution(execution);
        } else {
            execution.status = status_success();
            finalize_execution(execution, completion);
        }
    }

    /// This will set the current task to running state and emit an event that
    /// wakes up off-chain service which will execute the task.
    fun schedule_current_task_for_execution(
        execution: &mut ClusterExecution,
    ) {
        let curr_task_name = execution.current_task;
        let task_state = execution.tasks.borrow_mut(curr_task_name);

        // the task must yet to be scheduled
        assert!(task::get_state_status(task_state) == status_idle(), ECurrentTaskNotIdle);

        // useful for the first task when execution is in idle state
        execution.status = status_running();

        let (task_index, task) = current_task(execution);
        let tool = task.get_tool();
        let agent = execution.blueprint.agents.get(&task.get_agent_name());

        let task_prompt = task.get_prompt();
        let context = build_context(execution, task_index);
        let agent_model = agent.get_model_info();

        let execution_id = object::id(execution);
        let task_state = execution.tasks.borrow_mut(curr_task_name);
        task_state.set_state_status(status_running());

        let mut final_prompt = string::utf8(b"");
        final_prompt.append(context);
        final_prompt.append(string::utf8(b"\n\nTask: "));
        final_prompt.append(task_prompt);

        // Off-chain node that runs the model's inference will pick up the event
        // and submit completion with [`submit_completion`].
        prompt::emit_request_for_completion(
            &agent_model,
            string::utf8(b""),
            final_prompt,
            hash::sha3_256(*string::bytes(&final_prompt)),
            1000, // TODO: Get max tokens from the Agent
            70, // TODO: Get temperature from the Agent
            vector::empty<u8>(),
            execution_id,
            tool,
        );
    }

    /// The justification for building the context on-chain as opposed to
    /// fetching the execution state off-chain and building it there is that it
    /// simplifies the inference node's logic, in particular avoids a GET call
    /// to the APIs to fetch the object.
    fun build_context(
        execution: &ClusterExecution,
        task_index: u64,
    ): String {
        let mut context = string::utf8(b"");

        // Add memory context
        let memory_context = get_context(
            &execution.memory, PastNMessagesToIncludeInContext,
        );
        string::append(&mut context, memory_context);

        // Add previous task's context if it exists
        if (task_index > 0) {
            let prev_task_name = execution
                .blueprint
                .tasks
                .borrow(task_index - 1)
                .get_name();
            let prev_task_state = table::borrow(&execution.tasks, prev_task_name);
            let input_context = task::get_state_input_context(prev_task_state);
            if (!string::is_empty(&input_context)) {
                string::append(&mut context, string::utf8(b"\nPrevious Task Context: "));
                string::append(&mut context, input_context);
            };
        };

        context
    }

    fun add_message(
        memory: &mut Memory,
        role: String,
        content: String,
        name: Option<String>,
    ) {
        memory.messages.push_back(Message { role, content, name });
    }

    fun get_context(memory: &Memory, max_messages: u64): String {
        let mut context = string::utf8(b"");
        let len = memory.messages.length();
        let start = if (len > max_messages) { len - max_messages } else { 0 };

        let mut i = start;
        while (i < len) {
            let message = memory.messages.borrow(i);
            string::append(&mut context, message.role);
            string::append(&mut context, string::utf8(b": "));
            string::append(&mut context, message.content);
            string::append(&mut context, string::utf8(b"\n"));
            i = i + 1;
        };

        context
    }

    fun finalize_execution(
        execution: &mut ClusterExecution,
        completion: String,
    ) {
        // Get the last task's response (completion)
        let final_response = completion;

        // Convert the final_response to a vector<u8>
        let response_bytes = *string::bytes(&final_response);

        // Update the execution object
        execution.cluster_response = final_response;
        execution.status = status_success();

        // Emit the response to the user
        event::emit(ClusterResponseEvent {
            cluster: object::id(execution),
            cluster_name: execution.blueprint.name,
            response: response_bytes,
        });
    }

    /// Returns the index of the task within the blueprint's task vector and
    /// reference to the task itself.
    fun current_task(self: &ClusterExecution): (u64, &TaskBlueprint) {
        find_task(&self.blueprint, self.current_task)
    }

    /// Returns the index of the task within the blueprint's task vector and
    /// reference to the task itself.
    fun find_task(blueprint: &ClusterBlueprint, needle: TaskName): (u64, &TaskBlueprint) {
        let mut i = 0;
        while (i < vector::length(&blueprint.tasks)) {
            let task = vector::borrow(&blueprint.tasks, i);
            if (task::get_name(task) == needle) {
                return (i, task)
            };

            i = i + 1;
        };

        std::debug::print(&utf8(b"Task not found"));
        std::debug::print(&needle);
        abort ETaskNotFound
    }

    /// Same as `find_task` but returns a mutable reference to the task.
    fun find_task_mut(blueprint: &mut ClusterBlueprint, needle: TaskName): (u64, &mut TaskBlueprint) {
        let mut i = 0;
        while (i < vector::length(&blueprint.tasks)) {
            let task = vector::borrow_mut(&mut blueprint.tasks, i);
            if (task::get_name(task) == needle) {
                return (i, task)
            };

            i = i + 1;
        };

        std::debug::print(&utf8(b"Task not found"));
        std::debug::print(&needle);
        abort ETaskNotFound
    }
}
