# Stage 1: Build sui tools and dependencies
ARG SUI_TAG=testnet-v1.29.1
FROM talus-network/sui-tools:${SUI_TAG} AS sui-builder

FROM python:3.9-slim-bullseye

ENV PYTHONUNBUFFERED=1
ENV TARGET_DIR=/opt/sui/genesis/files 

RUN apt-get update && apt-get install -y libpq5 libpq-dev ca-certificates libc6

WORKDIR /opt/sui/genesis

# Copy necessary sui binary and libraries from the sui-builder stage
COPY --from=sui-builder /usr/local/bin/sui /usr/local/bin/sui

# Copy the necessary files for genesis creation
COPY overlays overlays
COPY static static
COPY compose-validators.yaml compose-validators.yaml
COPY requirements.txt .
COPY generate.py .

# Install Python dependencies for genesis preparation
RUN python3 -m pip install -r requirements.txt

# Set the entrypoint to run the generation script with the target directory
CMD ["/bin/bash", "-c", "python3 generate.py --genesis-template compose-validators.yaml --target-directory ${TARGET_DIR}"]
