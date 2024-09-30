import argparse
import ollama


class Inference:
    @staticmethod
    def prompt(prompt, model, max_tokens=1000, temperature=1.0):
        options = {"temperature": temperature, "num_predict": max_tokens}

        response = ollama.chat(
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


def main():
    parser = argparse.ArgumentParser(description="Test Ollama chat with Mistral model")
    parser.add_argument("prompt", help="The prompt to send to the model")
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1000,
        help="Maximum number of tokens to generate",
    )
    parser.add_argument(
        "--temperature", type=float, default=1.0, help="Temperature for text generation"
    )

    args = parser.parse_args()

    model = "mistral-latest"

    print(f"Testing Ollama chat with model: {model}")
    print(f"Prompt: {args.prompt}")
    print(f"Max tokens: {args.max_tokens}")
    print(f"Temperature: {args.temperature}")
    print("\nGenerating response...\n")

    try:
        response = Inference.prompt(
            args.prompt, model, args.max_tokens, args.temperature
        )
        print("Response:")
        print(response["message"]["content"])
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
