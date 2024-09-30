import sys
import json
from pathlib import Path
import requests
import os
from pydantic import BaseModel, Field

root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))
from pydantic import BaseModel, Field
from typing import Any, Union, Callable

from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import (
    ArxivQueryRun,
    PubmedQueryRun,
    SceneXplainTool,
    ShellTool,
)
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL
from langchain_community.tools import (
    ReadFileTool as LangchainReadFileTool,
    ListDirectoryTool as LangchainListDirectoryTool,
)
import google.generativeai as genai
from crewai_tools import BaseTool
from openai import OpenAI
from unstructured.partition.html import partition_html

from dotenv import load_dotenv

load_dotenv()
import os

# Load API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SCENEX_API_KEY = os.getenv("SCENEX_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)


class GeminiToolArgs(BaseModel):
    prompt: str = Field(..., description="The prompt for the Gemini model")
    model: str = Field(default="gemini-pro", description="The Gemini model to use")


class SearchToolArgs(BaseModel):
    query: str = Field(..., description="The search query to be used")
    num_results: str = Field(..., description="Number of results to return")


class WikipediaToolArgs(BaseModel):
    query: str = Field(..., description="The Wikipedia query to be used")


class ArxivToolArgs(BaseModel):
    query: str = Field(..., description="The Arxiv query to be used")


class PubmedToolArgs(BaseModel):
    query: str = Field(..., description="The Pubmed query to be used")


class SceneExplainToolArgs(BaseModel):
    image_url: str = Field(..., description="The URL of the image to be explained")


class ShellToolArgs(BaseModel):
    command: str = Field(..., description="The shell command to be executed")


class TavilySearchToolArgs(BaseModel):
    query: str = Field(..., description="The Tavily search query to be used")


class PythonREPLToolArgs(BaseModel):
    code: str = Field(..., description="The Python code to be executed")


class ReadFileToolArgs(BaseModel):
    file_path: str = Field(..., description="The path of the file to be read")


class ListDirectoryToolArgs(BaseModel):
    directory_path: str = Field(
        ..., description="The path of the directory to be listed"
    )


class GPT4VisionToolArgs(BaseModel):
    image_url: str = Field(..., description="The URL of the image to analyze")
    prompt: str = Field(..., description="The prompt for image analysis")


class DALLE3ToolArgs(BaseModel):
    prompt: str = Field(..., description="The prompt for image generation")


class OpenAIEmbeddingsToolArgs(BaseModel):
    text: str = Field(..., description="The text to create embeddings for")


ToolArgs = Union[
    SearchToolArgs,
    WikipediaToolArgs,
    ArxivToolArgs,
    PubmedToolArgs,
    SceneExplainToolArgs,
    ShellToolArgs,
    TavilySearchToolArgs,
    PythonREPLToolArgs,
    ReadFileToolArgs,
    ListDirectoryToolArgs,
    GPT4VisionToolArgs,
    DALLE3ToolArgs,
    OpenAIEmbeddingsToolArgs,
]


class ToolCallBody(BaseModel):
    tool_name: str = Field(..., description="Name of the tool to call")
    args: ToolArgs


def create_clusterai_tool(
    tool_name: str, tool_description: str, my_lambda_function: Callable[..., Any]
) -> BaseTool:
    class CustomTool(BaseTool):
        name: str = tool_name
        description: str = tool_description
        function: Callable[..., Any] = my_lambda_function

        def __init__(self):
            super().__init__()

        def _run(self, **kwargs: Any) -> Any:
            return self.function(**kwargs)

    return CustomTool()


class BrowserTools:
    @staticmethod
    def scrape_and_summarize_website(url: str) -> str:
        browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
        if not browserless_api_key:
            return "Error: BROWSERLESS_API_KEY is not set in the environment variables."

        browserless_url = (
            f"https://chrome.browserless.io/content?token={browserless_api_key}"
        )
        payload = json.dumps({"url": url})
        headers = {"cache-control": "no-cache", "content-type": "application/json"}

        try:
            response = requests.post(browserless_url, headers=headers, data=payload)
            response.raise_for_status()
            elements = partition_html(text=response.text)
            content = "\n\n".join([str(el) for el in elements])

            # Simple summarization (you may want to implement a more sophisticated summarization method)
            summary = content[:1000] + "..." if len(content) > 1000 else content
            return f"Summary of {url}:\n\n{summary}"
        except requests.RequestException as e:
            return f"Error scraping website: {str(e)}"


class InstagramSearchTools:
    @staticmethod
    def search_instagram(query: str) -> str:
        instagram_query = f"site:instagram.com {query}"
        search_tool = DuckDuckGoSearchRun()
        results = search_tool.run(instagram_query)
        return f"Instagram search results for '{query}':\n\n{results}"


class BrowserToolArgs(BaseModel):
    url: str = Field(..., description="The URL of the website to scrape and summarize")


class InstagramSearchToolArgs(BaseModel):
    query: str = Field(..., description="The Instagram-specific search query")


TOOL_ARGS_MAPPING = {
    "gemini": GeminiToolArgs,
    "search": SearchToolArgs,
    "wikipedia": WikipediaToolArgs,
    "arxiv": ArxivToolArgs,
    "pubmed": PubmedToolArgs,
    "scene_explain": SceneExplainToolArgs,
    "shell": ShellToolArgs,
    "tavily_search": TavilySearchToolArgs,
    "python_repl": PythonREPLToolArgs,
    "read_file": ReadFileToolArgs,
    "list_directory": ListDirectoryToolArgs,
    "gpt4_vision": GPT4VisionToolArgs,
    "dalle3": DALLE3ToolArgs,
    "openai_embeddings": OpenAIEmbeddingsToolArgs,
    "browser": BrowserToolArgs,
    "instagram_search": InstagramSearchToolArgs,
}

TOOLS = {
    "gemini": create_clusterai_tool(
        "gemini",
        "Useful for generating text using Google's Gemini AI model.",
        lambda prompt, model="gemini-pro": genai.GenerativeModel(model)
        .generate_content(prompt)
        .text,
    ),
    "search": create_clusterai_tool(
        "search",
        "Useful for searching the web for current information.",
        lambda query, num_results: DuckDuckGoSearchRun().run(
            f"{query} num_results={num_results}"
        ),
    ),
    "wikipedia": create_clusterai_tool(
        "wikipedia",
        "Useful for querying Wikipedia for general knowledge.",
        lambda query: WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()).run(query),
    ),
    "arxiv": create_clusterai_tool(
        "arxiv",
        "Useful for searching academic papers on arXiv.",
        lambda query: ArxivQueryRun().run(query),
    ),
    "pubmed": create_clusterai_tool(
        "pubmed",
        "Useful for searching medical and life sciences literature.",
        lambda query: PubmedQueryRun().run(query),
    ),
    "scene_explain": create_clusterai_tool(
        "scene_explain",
        "Useful for explaining the contents of an image.",
        lambda image_url: SceneXplainTool(api_key=SCENEX_API_KEY).run(image_url),
    ),
    "shell": create_clusterai_tool(
        "shell",
        "Useful for running shell commands.",
        lambda command: ShellTool().run(command),
    ),
    "tavily_search": create_clusterai_tool(
        "tavily_search",
        "Useful for performing searches using Tavily.",
        lambda query: json.dumps(
            TavilySearchResults(api_key=TAVILY_API_KEY).run(query)
        ),
    ),
    "python_repl": create_clusterai_tool(
        "python_repl",
        "Useful for executing Python code.",
        lambda code: PythonREPL().run(code),
    ),
    "read_file": create_clusterai_tool(
        "read_file",
        "Useful for reading the contents of a file.",
        lambda file_path: LangchainReadFileTool().run(file_path),
    ),
    "list_directory": create_clusterai_tool(
        "list_directory",
        "Useful for listing the contents of a directory.",
        lambda directory_path: LangchainListDirectoryTool().run(directory_path),
    ),
    "gpt4_vision": create_clusterai_tool(
        "gpt4_vision",
        "Useful for analyzing images using GPT-4 Vision.",
        lambda image_url, prompt: OpenAI(api_key=OPENAI_API_KEY)
        .chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=300,
        )
        .choices[0]
        .message.content,
    ),
    "dalle3": create_clusterai_tool(
        "dalle3",
        "Useful for generating images based on text prompts.",
        lambda prompt: OpenAI(api_key=OPENAI_API_KEY)
        .images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        .data[0]
        .url,
    ),
    "openai_embeddings": create_clusterai_tool(
        "openai_embeddings",
        "Useful for creating text embeddings using OpenAI's API.",
        lambda text: json.dumps(
            OpenAI(api_key=OPENAI_API_KEY)
            .embeddings.create(model="text-embedding-ada-002", input=text)
            .data[0]
            .embedding
        ),
    ),
    "browser": create_clusterai_tool(
        "browser",
        "Useful for browsing websites and summarizing their content.",
        lambda url: BrowserTool().run(url),
    ),
    "instagram_search": create_clusterai_tool(
        "instagram_search",
        "Useful for searching Instagram for images and videos.",
        lambda query: InstagramSearchTools.search_instagram(query),
    ),
}
