import json
from typing import Any, Iterator, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from langchain_community.llms.ollama import OllamaEndpointNotFoundError, _OllamaCommon


class TalusChatOllama(BaseChatModel, _OllamaCommon):
    def __init__(
        self,
        prompt_contract: Any,
        completion_contract: Any,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.prompt_contract = prompt_contract
        self.completion_contract = completion_contract

    @property
    def _llm_type(self) -> str:
        return "blockchain-ollama-chat"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Call the prompt contract to retrieve the prompt
        prompt = self.prompt_contract.get_prompt()

        # Convert the prompt to the format expected by Ollama
        ollama_messages = self._convert_messages_to_ollama_messages([prompt])

        # Call the Ollama API to generate the completion
        final_chunk = self._chat_stream_with_aggregation(
            ollama_messages,
            stop=stop,
            run_manager=run_manager,
            verbose=self.verbo**kwargs,
        )

        # Extract the generated text from the final chunk
        generated_text = final_chunk.text

        # Call the completion contract to store the completion
        self.completion_contract.store_completion(generated_text)

        # Create a ChatGeneration object with the generated text
        chat_generation = ChatGeneration(
            message=AIMessage(content=generated_text),
            generation_info=final_chunk.generation_info,
        )

        return ChatResult(generations=[chat_generation])

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        raise NotImplementedError(
            "Streaming is not supported for BlockchainChatOllama."
        )
