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
