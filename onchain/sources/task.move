module talus::task {
    //! A task represents units of work within the Cluster's execution.
    //! It's always bound to a specific agent that is supposed to work on it.

    use std::string::{Self, String};
    use talus::agent::AgentName;
    use talus::consts::{status_idle, status_running, status_success};
    use talus::tool::Tool;

    // === Data models ===

    /// Defines specifically what's the agent supposed to do.
    public struct TaskBlueprint has store, copy, drop {
        /// Tasks are identified by their name.
        /// This implies that task name must be unique within a single
        /// [`talus::cluster::Cluster`].
        name: TaskName,
        /// Which agent is responsible for running this task to completion.
        /// This agent must exist within the same [`talus::cluster::Cluster`] as this
        /// task.
        agent: AgentName,
        description: String,
        expected_output: String,
        prompt: String,
        context: String,
        /// If provided then the node will execute this tool and use the result
        /// to run an inference using the prompt.
        /// The LLM output is then uploaded as the response for this task.
        tool: Option<Tool>,
    }

    /// Puts a task into a concrete situation.
    public struct TaskState has store {
        /// You can find the information about this task by searching the Cluster's
        /// tasks by name.
        name: TaskName,
        agent_name: AgentName,
        /// TBD: This is used to build context but it's never changed from its
        ///      initial value of empty string.
        input_context: String,
        /// Enumeration of
        /// - `StatusIdle`
        /// - `StatusRunning`
        /// - `StatusSuccess`
        ///
        /// We use string constants to be more friendly to explorers.
        status: String,
        prompt: Option<ID>,
        response: String,
    }

    /// Task name serves as an identifier for a task.
    public struct TaskName has store, copy, drop {
        inner: String,
    }

    // === Constructors ===

    /// Returns a new instance of a [`TaskBlueprint`].
    public fun new(
        name: TaskName,
        agent: AgentName,
        description: String,
        expected_output: String,
        prompt: String,
        context: String,
    ): TaskBlueprint {
        TaskBlueprint {
            name,
            description,
            expected_output,
            agent,
            prompt,
            context,
            tool: option::none(),
        }
    }

    /// Returns a new instance of a [`TaskBlueprint`]
    /// with a tool attached.
    public fun new_with_tool(
        name: TaskName,
        agent: AgentName,
        description: String,
        expected_output: String,
        prompt: String,
        context: String,
        tool: Tool,
    ): TaskBlueprint {
        TaskBlueprint {
            name,
            description,
            expected_output,
            agent,
            prompt,
            context,
            tool: option::some(tool),
        }
    }

    public fun new_state(
        name: TaskName,
        agent_name: AgentName,
    ): TaskState {
        TaskState {
            name,
            agent_name,
            input_context: string::utf8(b""),
            status: status_idle(),
            prompt: option::none(),
            response: string::utf8(b""),
        }
    }

    /// Create a new instance of a [`TaskName`] from given string.
    /// Name serves as an identifier.
    public fun into_name(s: String): TaskName {
        TaskName { inner: s }
    }

    /// Convert a [`TaskName`] into a string.
    public fun into_string(name: TaskName): String {
        name.inner
    }

    // === State management ===

    public fun attach_tool(self: &mut TaskBlueprint, tool: Tool) {
        self.tool = option::some(tool);
    }

    // === Accessors ===

    public fun get_agent_name(self: &TaskBlueprint): AgentName { self.agent }
    public fun get_context(self: &TaskBlueprint): String { self.context }
    public fun get_description(self: &TaskBlueprint): String { self.description }
    public fun get_expected_output(self: &TaskBlueprint): String { self.expected_output }
    public fun get_name(self: &TaskBlueprint): TaskName { self.name }
    public fun get_prompt(self: &TaskBlueprint): String { self.prompt }
    public fun get_tool(self: &TaskBlueprint): Option<Tool> { self.tool }

    public fun get_state_agent_name(self: &TaskState): AgentName { self.agent_name }
    public fun get_state_input_context(self: &TaskState): String { self.input_context }
    public fun get_state_output_bytes(self: &TaskState): vector<u8> { *string::bytes(&self.response) }
    public fun get_state_status(self: &TaskState): String { self.status }
    public fun is_idle(self: &TaskState): bool { self.status == status_idle() }
    public fun is_running(self: &TaskState): bool { self.status == status_running() }
    public fun is_successful(self: &TaskState): bool { self.status == status_success() }

    // === Package protected ===

    public(package) fun set_state_status(self: &mut TaskState, status: String) { self.status = status; }
    public(package) fun set_state_response(self: &mut TaskState, response: String) { self.response = response; }
    public(package) fun set_state_prompt(self: &mut TaskState, prompt: ID) { self.prompt = option::some(prompt); }

    // === Tests ===

    #[test_only]
    public fun create_test_state(agent: AgentName): TaskState {
        TaskState {
            agent_name: agent,
            name: into_name(string::utf8(b"Write Talus Poem")),
            input_context: string::utf8(b"Talus is a decentralized network focusing on AI and blockchain"),
            status: status_idle(),
            prompt: option::none(),
            response: string::utf8(b""),
        }
    }
}
