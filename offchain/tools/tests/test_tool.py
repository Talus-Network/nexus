"""
tests for /tool/use route in main.py
To run, execute "pytest tests/test_tool.py" from `tools` directory
"""

from fastapi.testclient import TestClient
from ..server.main import app
import pytest
import os

client = TestClient(app)


def test_gpt4_vision_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "gpt4_vision",
            "args": {
                "image_url": "https://i.imgur.com/Rr1jAAn.jpeg",
                "prompt": "Describe this image",
            },
        },
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_dalle3_tool():
    response = client.post(
        "/tool/use",
        json={"tool_name": "dalle3", "args": {"prompt": "A futuristic city"}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_openai_embeddings_tool():
    response = client.post(
        "/tool/use",
        json={"tool_name": "openai_embeddings", "args": {"text": "Test embedding"}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_search_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "search",
            "args": {"query": "FastAPI tutorial", "num_results": "5"},
        },
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_wikipedia_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "wikipedia",
            "args": {"query": "Python programming language"},
        },
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_arxiv_tool():
    response = client.post(
        "/tool/use", json={"tool_name": "arxiv", "args": {"query": "quantum computing"}}
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_pubmed_tool():
    response = client.post(
        "/tool/use", json={"tool_name": "pubmed", "args": {"query": "COVID-19 vaccine"}}
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_scene_explain_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "scene_explain",
            "args": {"image_url": "https://example.com/image.jpg"},
        },
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_shell_tool():
    response = client.post(
        "/tool/use",
        json={"tool_name": "shell", "args": {"command": "echo 'Hello, World!'"}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_tavily_search_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "tavily_search",
            "args": {"query": "latest AI breakthroughs"},
        },
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_python_repl_tool():
    response = client.post(
        "/tool/use",
        json={"tool_name": "python_repl", "args": {"code": "print('Hello, World!')"}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_read_file_tool():
    # Create a temporary file for testing
    with open("test_file.txt", "w") as f:
        f.write("Test content")

    response = client.post(
        "/tool/use",
        json={"tool_name": "read_file", "args": {"file_path": "test_file.txt"}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()

    # Clean up the temporary file
    os.remove("test_file.txt")


def test_list_directory_tool():
    response = client.post(
        "/tool/use",
        json={"tool_name": "list_directory", "args": {"directory_path": "."}},
    )
    print(f"Response content: {response.json()}")
    assert response.status_code == 200
    assert "result" in response.json()


def test_invalid_tool():
    response = client.post(
        "/tool/use",
        json={
            "tool_name": "invalid_tool",
            "args": {"query": "test query", "num_results": "5"},
        },
    )
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.json()}")
    print(f"Response headers: {response.headers}")
    assert (
        response.status_code == 400
    ), f"Expected 400, got {response.status_code}. Response: {response.json()}"


def test_invalid_args():
    response = client.post(
        "/tool/use", json={"tool_name": "search", "args": {"invalid_arg": "value"}}
    )
    assert response.status_code == 422  # Validation error
