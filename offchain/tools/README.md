# Tools

This directory contains offchain tools for LLM inference and other functionalities.

## Model Inference

Model inference currently relies on ollama through the [server/main.py][main_py] route `/predict`, which runs inference
of the defined ollama models.

## Tools

Available tools are defined in [server/tools/tools.py][tools_py]. Current supported tools are listed
below and any desired tools can be added by following the instructions in **Adding Tools**.
Tools are executed through the [server/main.py][main_py] route `/tool/use`.

_Note_: to use the OpenAI, Gemini, Scenexplain, or Tavily tools, equivalent api keys must be set in the `.env` and can be obtained here:

- [OpenAI Key](https://openai.com/index/openai-api/)
- [Scenex Key](https://scenex.jina.ai/api)
- [Tavily Key](https://app.tavily.com)

The above tools can also be deleted if not desired for simplicity.

### Adding Tools

In [server/tools/tools.py][tools_py], each tool has a defined argument structure which inherits from `pydantic` `BaseModel`,
and a `ToolCallBody` which consists of their name and the argument substructure.
`TOOL_ARGS_MAPPING` is a dictionary of available tools and their args, and `TOOLS` is a dictionary of available tools
and their actual executables, wrapped by the `create_clusterai_tool` function which allows for any lambda
function to be defined as a tool. This setup was intended towards support of definition of tools from onchain.

### Supported Tools

1. `search`: Web search using DuckDuckGo.
2. `wikipedia`: Query Wikipedia for information.
3. `arxiv`: Search academic papers on arXiv.
4. `pubmed`: Search medical and life sciences literature.
5. `scene_explain`: Explain the contents of an image.
6. `shell`: Execute shell commands.
7. `tavily_search`: Perform searches using Tavily.
8. `python_repl`: Execute Python code.
9. `read_file`: Read the contents of a file.
10. `list_directory`: List the contents of a directory.
11. `gpt4_vision`: Analyze images using GPT-4 Vision.
12. `dalle3`: Generate images based on text prompts.
13. `openai_embeddings`: Create text embeddings using OpenAI's API.
14. `browser`: Scrape and summarize website content.
15. `instagram_search`: Search for Instagram-specific content.

Note: Each tool accepts specific arguments as defined in the `TOOL_ARGS_MAPPING` in the `tools.py` file. The AI model can use these tools by specifying the tool name and providing the required arguments.

## Tests

To run the tests:

```bash
pip3 install pytest
PYTHONPATH=src pytest tests
```

<!-- References -->
[main_py]: ./server/main.py
[tools_py]: ./server/tools/tools.py