module talus::prompt {
    //! A prompt represents a request for a model to generate a response.
    //!
    //! The [`RequestForCompletionEvent`] is emitted every time cluster execution
    //! is in need of a completion.
    //! The off-chain node that runs the model's inference listens to this event
    //! and submits the completion back to the chain.

    use std::string::{Self, String};
    use sui::event;
    use talus::model::{Self, ModelInfo};
    use talus::tool::Tool;

    // === Errors ===

    const EPromptCannotBeEmpty: u64 = 1;
    const ETemperatureMustBeBetweenHundredAndZero: u64 = 2;

    // === Events ===

    public struct RequestForCompletionEvent has copy, drop {
        cluster_execution: ID,
        node: ID,
        model: ID,
        external_provider: String,
        model_name: String,
        prompt_contents: String,
        prompt_hash: vector<u8>,
        max_tokens: u64,
        /// A value between 0 and 100.
        temperature: u8,
        extra_arguments: vector<u8>,
        tool: Option<Tool>,
    }

    // === Package protected ===

    /// Emits an event that's listened to by the off-chain node that runs the
    /// model.
    ///
    /// This is called within the context of the cluster execution hence package
    /// protected.
    public(package) fun emit_request_for_completion(
        model: &ModelInfo,
        external_provider: String,
        prompt_contents: String,
        prompt_hash: vector<u8>,
        max_tokens: u64,
        temperature: u8, // 0-200
        extra_arguments: vector<u8>,
        cluster_execution: ID,
        tool: Option<Tool>,
    ) {
        assert!(temperature <= 200, ETemperatureMustBeBetweenHundredAndZero);
        assert!(temperature >= 0, ETemperatureMustBeBetweenHundredAndZero);
        assert!(string::length(&prompt_contents) > 0, EPromptCannotBeEmpty);

        event::emit(RequestForCompletionEvent {
            node: model::get_node_id(model),
            model: model::get_id(model),
            cluster_execution,
            model_name: model::get_name(model),
            external_provider: external_provider,
            prompt_contents,
            prompt_hash,
            max_tokens,
            temperature,
            extra_arguments,
            tool,
        });
    }
}
