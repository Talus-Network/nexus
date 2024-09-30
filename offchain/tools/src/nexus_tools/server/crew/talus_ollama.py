### This class will basically overrides the LLM implementaion for Ollama as we added
### the ability to report usage per agent request, the logic here is to be able to chrage


import json
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union, cast

from langchain_core._api import deprecated
from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    ChatMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from langchain_community.llms.ollama import OllamaEndpointNotFoundError, _OllamaCommon


class TalusOllama(BaseChatModel, _OllamaCommon):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prompt_tokens = 0
        self.completion_tokens = 0

    @property
    def _llm_type(self) -> str:
        return "talus-ollama-chat"

    def _convert_messages_to_ollama_messages(
        self, messages: List[BaseMessage]
    ) -> List[Dict[str, Union[str, List[str]]]]:
        ollama_messages: List = []
        for message in messages:
            role = ""
            if isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            elif isinstance(message, SystemMessage):
                role = "system"
            else:
                raise ValueError("Received unsupported message type for Ollama.")

            content = ""
            images = []
            if isinstance(message.content, str):
                content = message.content
            else:
                for content_part in cast(List[Dict], message.content):
                    if content_part.get("type") == "text":
                        content += f"\n{content_part['text']}"
                    elif content_part.get("type") == "image_url":
                        if isinstance(content_part.get("image_url"), str):
                            image_url_components = content_part["image_url"].split(",")
                            if len(image_url_components) > 1:
                                images.append(image_url_components[1])
                            else:
                                images.append(image_url_components[0])
                        else:
                            raise ValueError(
                                "Only string image_url content parts are supported."
                            )
                    else:
                        raise ValueError(
                            "Unsupported message content type. "
                            "Must either have type 'text' or type 'image_url' "
                            "with a string 'image_url' field."
                        )

            ollama_messages.append(
                {
                    "role": role,
                    "content": content,
                    "images": images,
                }
            )

        return ollama_messages

    def _create_chat_stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        payload = {
            "model": self.model,
            "messages": self._convert_messages_to_ollama_messages(messages),
        }
        self.prompt_tokens = self._count_tokens(payload)
        self.report_prompt_charges()  # Report prompt charges before calling LLM
        yield from self._create_stream(
            payload=payload, stop=stop, api_url=f"{self.base_url}/api/chat", **kwargs
        )

    def _chat_stream_with_aggregation(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        verbose: bool = False,
        **kwargs: Any,
    ) -> ChatGenerationChunk:
        final_chunk: Optional[ChatGenerationChunk] = None
        for stream_resp in self._create_chat_stream(messages, stop, **kwargs):
            if stream_resp:
                chunk = _chat_stream_response_to_chat_generation_chunk(stream_resp)
                if final_chunk is None:
                    final_chunk = chunk
                else:
                    final_chunk += chunk
                if run_manager:
                    run_manager.on_llm_new_token(
                        chunk.text,
                        chunk=chunk,
                        verbose=verbose,
                    )
        if final_chunk is None:
            raise ValueError("No data received from Ollama stream.")

        self.completion_tokens = self._count_tokens(final_chunk.text)
        self.report_completion_charges()  # Report completion charges after receiving from LLM
        return final_chunk

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        final_chunk = self._chat_stream_with_aggregation(
            messages,
            stop=stop,
            run_manager=run_manager,
            verbose=self.verbose,
            **kwargs,
        )
        chat_generation = ChatGeneration(
            message=AIMessage(content=final_chunk.text),
            generation_info=final_chunk.generation_info,
        )
        return ChatResult(generations=[chat_generation])

    def _count_tokens(self, text: Union[str, Dict]) -> int:
        # TODO: Implement token counting logic based on your specific requirements
        # This is a placeholder implementation
        if isinstance(text, str):
            return len(text.split())
        elif isinstance(text, Dict):
            return sum(len(str(value).split()) for value in text.values())
        else:
            raise ValueError("Unsupported text type for token counting.")

    def report_prompt_charges(self) -> None:
        # TODO: Implement the logic to report prompt charges to the blockchain
        print(f"Reporting prompt charges: {self.prompt_tokens} tokens")

    def report_completion_charges(self) -> None:
        # TODO: Implement the logic to report completion charges to the blockchain
        print(f"Reporting completion charges: {self.completion_tokens} tokens")
