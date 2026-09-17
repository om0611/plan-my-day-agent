import asyncio
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from date_tools import format_to_rfc3339, get_datetime_context
from visualizer import (
    display_agent_response,
    display_error,
    display_goodbye,
    display_success,
    display_thought,
    display_tool_call,
    display_tool_result,
    display_welcome_banner,
    get_user_input,
    thinking_status,
)

load_dotenv()


SYSTEM_PROMPT = """
You are a day planner agent. You help users plan, organize, and manage their daily 
schedule and calendar events.

CRITICAL: You must always obtain the current date and time context using the 
`get_datetime_context` tool before doing anything else to stay current with the present
day.
"""


def extract_text(content: Any) -> str:
    """Extract string content from string or structured content lists."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)


async def main():
    display_welcome_banner()

    model = ChatOllama(
        model="gemma4:31b-cloud",
        base_url="https://ollama.com",
        temperature=0,
    )
    tools = []

    # Connect to Calendar MCP Client
    client = MultiServerMCPClient(
        {
            "calendar": {
                "transport": "http",
                "url": "http://localhost:8000/mcp",
            },
        }
    )

    try:
        mcp_tools = await client.get_tools()
        tools.extend(mcp_tools)
        display_success("Connected to Calendar MCP server.")
    except Exception as e:
        display_error(f"MCP server unreachable: {e}")
        return

    # Add custom date tools
    tools.append(get_datetime_context)
    tools.append(format_to_rfc3339)

    # Create agent
    agent = create_agent(
        model,
        tools,
        system_prompt=SYSTEM_PROMPT,
    )

    while True:
        user_input = get_user_input()
        if user_input is None or user_input.lower() in ("q", "quit", "exit"):
            display_goodbye()
            break

        if not user_input:
            continue

        tool_name_map = {}
        try:
            with thinking_status():
                async for chunk in agent.astream(
                    {"messages": [{"role": "user", "content": user_input}]},
                    stream_mode="updates",
                ):
                    for _node_name, node_output in chunk.items():
                        messages = node_output.get("messages", [])
                        for msg in messages:
                            if isinstance(msg, AIMessage) or hasattr(msg, "tool_calls"):
                                tool_calls = getattr(msg, "tool_calls", None)
                                if tool_calls:
                                    raw_content = getattr(msg, "content", "")
                                    content_text = extract_text(raw_content).strip()
                                    if content_text:
                                        display_thought(content_text)
                                    for tc in tool_calls:
                                        tc_id = tc.get("id")
                                        tc_name = tc.get("name", "unknown_tool")
                                        tc_args = tc.get("args", {})
                                        if tc_id:
                                            tool_name_map[tc_id] = tc_name
                                        display_tool_call(tc_name, tc_args)
                                else:
                                    raw_content = getattr(msg, "content", "")
                                    content_text = extract_text(raw_content).strip()
                                    if content_text:
                                        display_agent_response(content_text)
                            elif (
                                isinstance(msg, ToolMessage)
                                or msg.__class__.__name__ == "ToolMessage"
                            ):
                                call_id = getattr(msg, "tool_call_id", None)
                                tool_name = getattr(
                                    msg, "name", None
                                ) or tool_name_map.get(call_id, "Tool")
                                result_content = getattr(msg, "content", "")
                                display_tool_result(tool_name, result_content)
        except Exception as e:
            display_error(f"Error during execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
