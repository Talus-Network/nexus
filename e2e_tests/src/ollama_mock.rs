//! If ollama http API env var is not provided, we spawn a simple HTTP server
//! to mock those APIs that return a static response.

use {
    crate::prelude::*,
    axum::{routing::post, Router},
    reqwest::Url,
    std::str::FromStr,
};

pub(crate) async fn start() -> Result<Url> {
    let app = Router::new().route("/", post(mocked_model_response));

    let addr = "0.0.0.0:3000";
    let listener = tokio::net::TcpListener::bind(addr).await?;

    tokio::spawn(async move {
        if let Err(err) = axum::serve(listener, app).await {
            error!("Failed to start mock ollama HTTP server: {err}");
        }
    });

    Ok(FromStr::from_str(&format!("http://{addr}"))?)
}

/// Prints "This is a mock LLM response." and is done.
async fn mocked_model_response() -> &'static str {
    r#"{"model":"mistral","created_at":"2024-08-07T10:08:39.33050386Z","response":" \"","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.330506894Z","response":"This","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.333717178Z","response":" is","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.346571008Z","response":" a","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.359445086Z","response":" mock","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.372366904Z","response":" LL","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.385213658Z","response":"M","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.39866316Z","response":" response","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.411548254Z","response":".\"","done":false}
{"model":"mistral","created_at":"2024-08-07T10:08:39.425126938Z","response":"","done":true,"done_reason":"stop","context":[3,29473,2066,16650,3095,29515,1619,1117,1032,9743,9582,29487,3667,4,1027,1113,4028,1117,1032,9743,17472,29523,3667,1379],"total_duration":183077547,"load_duration":3397703,"prompt_eval_count":16,"prompt_eval_duration":20677000,"eval_count":10,"eval_duration":117239000}"#
}
