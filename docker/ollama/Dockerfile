FROM ollama/ollama:0.3.2

ARG LLAMA_MODEL_VERSION=llama

RUN apt-get update && apt-get install -y curl

RUN nohup bash -c "ollama serve &" && \
    until curl -s http://localhost:11434 | grep "Ollama is running"; do echo "Waiting for Ollama to start..."; sleep 2; done && \
    ollama pull ${LLAMA_MODEL_VERSION}

EXPOSE 11434

CMD ["serve"]