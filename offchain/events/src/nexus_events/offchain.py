import requests
import os
from dotenv import load_dotenv

load_dotenv()

LLM_ASSISTANT_URL = os.getenv("LLM_ASSISTANT_URL", "http://localhost:8080/predict")


class OffChain:
    def process(
        self, prompt: str, model_name: str, max_tokens: int, temperature: float
    ) -> str:
        url = LLM_ASSISTANT_URL
        headers = {"Content-Type": "application/json"}
        prompt_data = {
            "prompt": prompt,
            "model": model_name,
            "max_tokens": int(max_tokens),
            "temperature": temperature,
        }

        try:

            response = requests.post(url, headers=headers, json=prompt_data)
            response.raise_for_status()
            result = response.json()

            completion = result["completion"]
            return completion
        except requests.exceptions.RequestException as e:
            msg = f"Error occurred while calling the API: {e}"
            if hasattr(e, "response") and e.response is not None:
                msg += f"\nResponse content: {e.response.text}"
            print(msg)
            raise Exception(status_code=500, detail=msg)


def main():

    off_chain = OffChain()
    prompt = "Write python script that prints the numbers 1 to 100"
    model_name = "tinyllama"
    max_tokens = 3000
    temperature = 0.3

    completion = off_chain.process(prompt, model_name, max_tokens, temperature)
    print(completion)


if __name__ == "__main__":
    main()
