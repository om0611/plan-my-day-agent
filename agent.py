import asyncio

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama

from date_tools import format_to_rfc3339, get_datetime_context
from stream_handler import handle_stream
from visualizer import (
    display_error,
    display_goodbye,
    display_success,
    display_welcome_banner,
    get_user_input,
)

load_dotenv()


SYSTEM_PROMPT = """
You are a day planner agent. You help users plan, organize, and manage their daily 
schedule and calendar events.

CRITICAL: You must always obtain the current date and time context using the 
`get_datetime_context` tool before doing anything else to stay current with the present
day.
"""


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

        await handle_stream(agent, user_input)


if __name__ == "__main__":
    asyncio.run(main())
