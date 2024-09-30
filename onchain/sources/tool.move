module talus::tool {
    //! A tool is utility or resource that an agent can use to complete tasks.
    //! A tool is stored optionally on a [talus::task::Task] and if provided,
    //! the agent will use the result of the tool to submit a response.
    //! A tool can have side-effects.
    //!
    //! An example of a tool would be wiki search or a smart contract invocation.

    use std::string::String;

    // === Data models ===

    /// Tool name serves as an identifier for a tool.
    public struct Tool has store, copy, drop {
        name: String,
        /// At the moment tool can be parametrized only up front when creating a
        /// cluster.
        args: vector<String>,
    }

    // === Constructors ===

    public fun new(name: String, args: vector<String>): Tool {
        Tool { name, args }
    }

    // === Accessors ===

    public fun get_name(self: &Tool): String { self.name }
    public fun get_args(self: &Tool): vector<String> { self.args }
}
