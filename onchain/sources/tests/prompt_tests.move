#[test_only]
module talus::prompt_tests {
    use std::string;
    use sui::test_scenario::{Self, ctx};
    use talus::model;
    use talus::prompt;

    #[test]
    fun test_emit_request_for_completion() {
        let owner = @0x1;
        let mut scenario = test_scenario::begin(owner);

        // Create a mock Model
        let model = model::new_mock_info_for_testing(ctx(&mut scenario));

        test_scenario::next_tx(&mut scenario, owner);
        {
            let mock_execution_id = object::new(ctx(&mut scenario));

            prompt::emit_request_for_completion(
                &model,
                string::utf8(b"Test Provider"),
                string::utf8(b"Test prompt"),
                b"test_hash",
                100,
                50,
                vector::empty(),
                object::uid_to_inner(&mock_execution_id),
                option::none(), // no tool
            );

            object::delete(mock_execution_id);
        };

        test_scenario::end(scenario);
    }

    #[test]
    #[expected_failure(abort_code = prompt::ETemperatureMustBeBetweenHundredAndZero)]
    fun test_invalid_temperature() {
        let owner = @0x1;
        let mut scenario = test_scenario::begin(owner);

        // Create a mock Model
        let model = model::new_mock_info_for_testing(ctx(&mut scenario));

        test_scenario::next_tx(&mut scenario, owner);
        {
            let mock_execution_id = object::new(ctx(&mut scenario));
            prompt::emit_request_for_completion(
                &model,
                string::utf8(b"Test Provider"),
                string::utf8(b"Test prompt"),
                b"test_hash",
                100,
                201, // Invalid temperature
                vector::empty(),
                object::uid_to_inner(&mock_execution_id),
                option::none(), // no tool
            );

            object::delete(mock_execution_id);
        };

        test_scenario::end(scenario);
    }

    #[test]
    #[expected_failure(abort_code = prompt::EPromptCannotBeEmpty)]
    fun test_empty_prompt() {
        let owner = @0x1;
        let mut scenario = test_scenario::begin(owner);

        // Create a mock Model
        let model = model::new_mock_info_for_testing(ctx(&mut scenario));

        test_scenario::next_tx(&mut scenario, owner);
        {
            let mock_execution_id = object::new(ctx(&mut scenario));
            prompt::emit_request_for_completion(
                &model,
                string::utf8(b"Test Provider"),
                string::utf8(b""), // Empty prompt
                b"test_hash",
                100,
                50,
                vector::empty(),
                object::uid_to_inner(&mock_execution_id),
                option::none(), // no tool
            );

            object::delete(mock_execution_id);
        };

        test_scenario::end(scenario);
    }
}
