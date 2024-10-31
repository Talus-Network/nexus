import os
import ollama
from ollama import Client


class Inference:
    @staticmethod
    def prompt(prompt, model, max_tokens=1000, temperature=1.0):
        # Fetch the URL from environment variable, defaulting to localhost if not provided
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Create a custom client with the specified host
        client = Client(host=ollama_host)

        # Set up options for the request
        options = {"temperature": temperature, "num_predict": max_tokens}

        # Make the request using the client
        response = client.chat(
            model=model,
            options=options,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        return response
