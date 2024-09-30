# coding: utf-8

from fastapi.testclient import TestClient


from openapi_server.models.completion import Completion
from openapi_server.models.error import Error
from openapi_server.models.prompt import Prompt


def test_predict_post(client: TestClient):
    """Test case for predict_post

    Get a completion response from the AI model based on the provided prompt and parameters.
    """
    prompt = {
        "max_tokens": 1024,
        "temperature": 1.0,
        "model": "llama2-code",
        "text": "What is the capital of France?",
    }

    headers = {}
    response = client.request(
        "POST",
        "/predict",
        headers=headers,
        json=prompt,
    )

    # uncomment below to assert the status code of the HTTP response
    # assert response.status_code == 200
