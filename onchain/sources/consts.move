module talus::consts {
    use std::string::{String, utf8};

    // === Statuses ===

    const StatusIdle: vector<u8> = b"IDLE";
    public fun status_idle(): String { utf8(StatusIdle) }

    const StatusRunning: vector<u8> = b"RUNNING";
    public fun status_running(): String { utf8(StatusRunning) }

    const StatusSuccess: vector<u8> = b"SUCCESS";
    public fun status_success(): String { utf8(StatusSuccess) }
}
