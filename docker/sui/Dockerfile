#syntax=docker/dockerfile:1

FROM rust:1.81-bullseye AS builder

ARG PROFILE=release
ARG GIT_REVISION
ARG SUI_TAG=testnet-v1.29.1

ENV GIT_REVISION=$GIT_REVISION

RUN apt-get update && apt-get install -y git cmake clang libpq5 libpq-dev

WORKDIR /sui

RUN git clone --depth 1 --branch ${SUI_TAG} https://github.com/MystenLabs/sui.git .

RUN cargo build --profile ${PROFILE} \
    --bin sui-node \
    --bin sui \
    --bin sui-faucet 

FROM debian:bullseye-slim AS runtime

WORKDIR /sui

RUN apt-get update && apt-get install -y libpq5 libpq-dev ca-certificates git jq curl

COPY --from=builder /sui/target/release/sui-node /usr/local/bin
COPY --from=builder /sui/target/release/sui /usr/local/bin
COPY --from=builder /sui/target/release/sui-faucet /usr/local/bin

ARG BUILD_DATE
ARG GIT_REVISION
LABEL build-date=$BUILD_DATE
LABEL git-revision=$GIT_REVISION
