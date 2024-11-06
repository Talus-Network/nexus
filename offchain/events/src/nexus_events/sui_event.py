import asyncio
from pysui import SuiConfig
from pysui.sui.sui_clients.sync_client import SuiClient
import aiohttp
import ast
import argparse
import time
from pysui.sui.sui_types.collections import EventID
from pysui.sui.sui_types.event_filter import MoveEventTypeQuery
from typing import Any
import sys
import os
import signal

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, root_dir)
from nexus_tools.server.tools.tools import TOOLS, TOOL_ARGS_MAPPING
from pysui.sui.sui_clients.sync_client import SuiClient as SyncClient
from pysui.sui.sui_txn import SyncTransaction
from pysui.sui.sui_types.scalars import ObjectID, SuiString, SuiBoolean
from pysui.sui.sui_txresults.complex_tx import SubscribedEvent
from nexus_events.offchain import OffChain
import json
import unicodedata
import unidecode
import re
import traceback

# possible values TALUS_NODE, EXTERNAL_NODE
node_type = os.environ.get("NODE_TYPE", "TALUS_NODE")

off_chain = OffChain()


async def call_use_tool(name, args, url):
    """calls /tool/use endpoint with tool name and args, called by event handler"""
    print(f"Calling /tool/use with name: {name}, args: {args}, url: {url}")

    try:
        if name not in TOOLS:
            print(f"Tool '{name}' not found in TOOLS dictionary")
            print(f"Available tools: {list(TOOLS.keys())}")
            return None

        ToolArgsClass = TOOL_ARGS_MAPPING.get(name, None)
        if ToolArgsClass is None:
            print(f"No ToolArgs class found for tool: {name}")
            return None

        tool_args = ToolArgsClass(**dict(zip(ToolArgsClass.__fields__.keys(), args)))

        payload = {"tool_name": name, "args": tool_args.dict()}

        headers = {"Content-Type": "application/json"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 400 or response.status == 422:
                    error_detail = await response.text()
                    print(f"Error {response.status}: {error_detail}")
                    return None
                response.raise_for_status()
                result = await response.json()
                return result

    except Exception as e:
        print(f"Error in call_use_tool: {e}")
        return None


def sanitize_text(text):
    text = unidecode.unidecode(text)
    text = unicodedata.normalize("NFKD", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("…", "...").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^\x00-\x7F]+", "", text)
    text = "".join(char for char in text if ord(char) < 256)
    return text


async def prompt_event_handler(
    client: SuiClient,
    package_id: str,
    model_owner_cap_id: str,
    event: SubscribedEvent,
    tool_url: str,
) -> Any:
    """Handler captures the move event type for each received."""
    try:
        parsed_json = ast.literal_eval(event.parsed_json)

        model_name = parsed_json["model_name"]
        prompt = parsed_json["prompt_contents"]
        max_tokens = parsed_json["max_tokens"]
        temperature = parsed_json["temperature"] / 100
        cluster_execution_id = parsed_json["cluster_execution"]

        completion = ""
        if temperature < 0.0 or temperature > 2.0:
            print(
                f"Invalid temperature value {temperature}. Setting to default value of 1.0"
            )
            temperature = 1

        if parsed_json["tool"]:
            tool_name = parsed_json["tool"]["fields"]["name"]
            tool_args = parsed_json["tool"]["fields"]["args"]
            print(f"Calling tool '{tool_name}' with args: {tool_args}")

            tool_result = await call_use_tool(tool_name, tool_args, tool_url)
            tool_result = tool_result["result"]
            print(f"tool_result: {tool_result}")

            if tool_result:
                prompt = (
                    "context from" + tool_name + ": " + str(tool_result) + ". " + prompt
                )
            else:
                print(f"Error calling tool: {tool_name}")
                return None

    except Exception as e:
        print(f"Error extracting prompt info: {e}")

    print("Waiting for completion...")
    completion = off_chain.process(prompt, model_name, max_tokens, temperature)

    try:
        # Create the configuration
        txn = SyncTransaction(client=client)

        completion_json = json.loads(completion)
        completion = completion_json["message"]["content"]
        completion_safe = sanitize_text(completion)

        try:
            print("Submitting completion ...")
            result = txn.move_call(
                target=f"{package_id}::cluster::submit_completion_as_model_owner",
                arguments=[
                    ObjectID(cluster_execution_id),
                    ObjectID(model_owner_cap_id),
                    SuiString(completion_safe),
                ],
            )
        except ValueError as e:
            print(f"Error: {e}")
            return None
        except Exception as e:
            print(f"Error in create_completion: {e}")
            traceback.print_exc()
            return

        result = txn.execute(gas_budget=1000000000)
        if result.is_ok():
            print(
                f"Completion created in tx '{result.result_data.effects.transaction_digest}'"
            )
            return {"func": result.result_data}
        else:
            print(f"Completion creation transaction failed: {result.result_string}")
            return None
    except Exception as e:
        print(f"Error in create_completion: {e}")
        print(f"Error type: {type(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Listen for ToolUsed events on the Sui network"
    )
    parser.add_argument("--rpc", default="http://localhost:9000", help="RPC URL")
    parser.add_argument("--ws", default="ws://localhost:9000", help="WebSocket URL")
    parser.add_argument(
        "--packageid",
        default=(os.getenv("PACKAGE_ID")),
        help="Package ID to filter events (required)",
    )
    parser.add_argument(
        "--privkey",
        default=(os.getenv("SUI_PRIVATE_KEY")),
        help="Sui private key (required)",
    )
    parser.add_argument(
        "--modelownercapid",
        default=(os.getenv("MODEL_OWNER_CAP_ID")),
        help="Model owner capability object ID (required)",
    )
    parser.add_argument(
        "--toolurl",
        default="http://0.0.0.0:8080/tool/use",
        help="URL to call /tool/use endpoint",
    )

    args = parser.parse_args()

    package_id = args.packageid
    model_owner_cap_id = args.modelownercapid
    tool_url = args.toolurl

    config = SuiConfig.user_config(
        rpc_url=args.rpc, ws_url=args.ws, prv_keys=[args.privkey]
    )
    client = SuiClient(config)

    next_cursor = None
    while True:
        next_cursor = process_next_event_page(
            client,
            package_id,
            model_owner_cap_id,
            cursor=next_cursor,
            tool_url=tool_url,
        )


# Fetches the next page of events
#
# Returns a tuple:
# - The first element is the next cursor to use
# - The second element is a boolean indicating whether the first event should be skipped
def process_next_event_page(
    client: SuiClient,
    package_id: str,
    model_owner_cap_id: str,
    cursor: EventID,
    tool_url: str,
):
    prompt_event_type = f"{package_id}::prompt::RequestForCompletionEvent"
    event_filter = MoveEventTypeQuery(prompt_event_type)

    events_result = client.get_events(
        query=event_filter, descending_order=SuiBoolean(False), cursor=cursor
    )
    if events_result.is_err():
        print(f"Cannot read Sui events: {events_result.result_string}")
        sys.exit(1)

    events = events_result.result_data.data
    # If you needed to debug the events, print some information with this:
    for event in events:
        print(f"event_id: {event.event_id}, timestamp_ms: {event.timestamp_ms}")

    if not events:
        print(f"No new events, waiting...")
        time.sleep(3)
        return cursor

    print(f"Processing {len(events)} events")
    for event in events:
        asyncio.run(
            prompt_event_handler(
                client, package_id, model_owner_cap_id, event, tool_url
            )
        )

    # Set the cursor to the last event.
    # Also next fetch will skip the first event (the last event of this fetch)
    # since it will have been already processed.
    # We don't use the "next_cursor" property to simplify the code.

    last_event_id = events[-1].event_id
    event_seq = last_event_id["eventSeq"]
    tx_digest = last_event_id["txDigest"]
    next_cursor = EventID(event_seq, tx_digest)
    return next_cursor


if __name__ == "__main__":
    main()
