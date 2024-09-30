import sys
import logging
from pathlib import Path
import json
from typing import Dict

from .models.completion import Completion
from .models.error import Error
from .models.prompt import Prompt
from .controllers.inference import Inference
from .models.model import ModelsResponse
from .tools.tools import TOOLS, ToolCallBody

import ollama
from datetime import datetime
from fastapi import Body, FastAPI, HTTPException
from dotenv import load_dotenv

from langchain.prompts import PromptTemplate
from langchain_experimental.llms.ollama_functions import OllamaFunctions
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.runnables import RunnablePassthrough

from dotenv import load_dotenv  # New user: add .env file with oai key

load_dotenv()
import openai

# Add the root directory to PYTHONPATH
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Talus Model Integration API",
    description="Talus Utility for integrating Models trough API",
    version="6.0.2",
)

inference = Inference()


@app.post(
    "/predict",
    responses={
        200: {
            "model": Completion,
            "description": "The AI model successfully generated a completion.",
        },
        400: {
            "model": Error,
            "description": "The request body contains invalid parameters.",
        },
        500: {
            "model": Error,
            "description": "An unexpected error occurred while the server was processing the request.",
        },
    },
    tags=["default"],
    summary="Get a completion response from the AI model based on the provided prompt and parameters.",
    response_model_by_alias=True,
)
async def predict(
    prompt_data: Prompt = Body(..., description="The input data for the AI model.")
) -> Completion:
    """
    This endpoint processes the input prompt with specified parameters and returns the AI-generated completion.
    """
    print("start... predict")
    print(f"prompt_data: {prompt_data}")

    completion = inference.prompt(
        prompt=prompt_data.prompt,
        model=prompt_data.model,
        max_tokens=prompt_data.max_tokens,
        temperature=prompt_data.temperature,
    )
    print(f"completion: {completion}")

    return Completion(completion=json.dumps(completion), timestamp=datetime.now())


@app.post(
    "/tool/use",
    responses={
        200: {"model": dict, "description": "Successfully used the specified tool."},
        400: {
            "model": Error,
            "description": "The request body contains invalid parameters or unsupported tool.",
        },
        500: {
            "model": Error,
            "description": "An unexpected error occurred while processing the request.",
        },
    },
    tags=["default"],
    summary="Use a specified tool to process the provided query.",
    response_model_by_alias=True,
)
async def use_tool(tool_call_body: ToolCallBody) -> Dict[str, str]:
    """
    This endpoint processes the input query using the specified tool.
    Supported tools are in TOOLS
    """

    print(f"use tool called with: {tool_call_body}")
    if tool_call_body.tool_name not in TOOLS:
        raise HTTPException(
            status_code=400, detail=f"Unknown tool: {tool_call_body.tool_name}"
        )

    try:
        tool = TOOLS[tool_call_body.tool_name]
        result = tool._run(**tool_call_body.args.dict())
        print(f"tool result: {result}")
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="An error occurred while using the tool"
        )


# === The below is still in development ===


def complete_json(incomplete_json):
    try:
        # Try to parse as is
        return json.loads(incomplete_json)
    except json.JSONDecodeError:
        # If it fails, attempt to complete the JSON
        if incomplete_json.strip().endswith("}"):
            # If it ends with '}', assume it's just missing the final '}'
            return json.loads(incomplete_json + "}")
        elif '"tool_input": {' in incomplete_json:
            # If it has an incomplete tool_input, try to complete it
            return json.loads(incomplete_json + "}}")
        else:
            # If we can't easily complete it, raise an error
            raise ValueError(f"Unable to complete JSON: {incomplete_json}")


@app.post("/prompt_tools", response_model=Completion)
async def prompt_tools(prompt_data: Prompt = Body(...)):
    def wrap_clusterai_tool(tool):
        def wrapped(**kwargs):
            return tool._run(**kwargs)

        return wrapped

    wrapped_tools = {name: wrap_clusterai_tool(tool) for name, tool in TOOLS.items()}

    try:
        print(f"Received prompt: {prompt_data.prompt}")
        print(f"Selected tools: {prompt_data.tools}")

        llm = OllamaFunctions(
            model=prompt_data.model,
            temperature=prompt_data.temperature,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
            format="json",
        )
        print("OllamaFunctions initialized")

        selected_tools = []
        for tool_name in prompt_data.tools:
            if tool_name in TOOLS:
                tool = TOOLS[tool_name]
                selected_tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string"},
                            },
                            "required": ["query"],
                        },
                    }
                )
                print(f"Added tool: {tool.name}")
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        llm_with_tools = llm.bind_tools(selected_tools)
        print("Tools bound to LLM")

        prompt_template = PromptTemplate(
            input_variables=["input"],
            template="Answer the following question, using the provided tools if necessary. Always use a tool before answering: {input}",
        )
        print("Prompt template created")

        chain = {"input": RunnablePassthrough()} | prompt_template | llm_with_tools
        print("RunnableSequence created")

        print("Invoking the chain")
        result = chain.invoke(prompt_data.prompt)
        print(f"Chain result: {result}")

        # Process the result
        if isinstance(result, str):
            try:
                result_json = complete_json(result)
                if "tool" in result_json:
                    tool_name = result_json["tool"]
                    tool_input = result_json["tool_input"]
                    print(f"Executing tool: {tool_name} with input: {tool_input}")
                    tool_result = wrapped_tools[tool_name](**tool_input)
                    print(f"Tool result: {tool_result}")
                    final_result = f"Tool {tool_name} returned: {tool_result}"
                else:
                    final_result = json.dumps(result_json)
            except Exception as e:
                print(f"Error processing result: {e}")
                final_result = f"Error processing result: {result}"
        else:
            final_result = str(result)

        if not final_result:
            print("Chain returned an empty result")
            return Completion(
                completion="The model did not generate any output. Please try again.",
                timestamp=datetime.now(),
            )

        return Completion(completion=final_result, timestamp=datetime.now())

    except Exception as e:
        print(f"An error occurred in prompt_tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def execute_tool_call(tool_call):
    tool_name = tool_call["name"]
    args = tool_call["args"]

    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool = TOOLS[tool_name]
    return tool._run(**args)


@app.get("/models", response_model=ModelsResponse)
async def get_models() -> ModelsResponse:
    models_res = ollama.list()
    print(models_res["models"])
    return ModelsResponse(models=models_res["models"])
