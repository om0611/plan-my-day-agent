import asyncio
import datetime

from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from date_tools import format_to_rfc3339, get_datetime_context

load_dotenv()


async def main():
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
    except Exception as e:
        print(f"MCP server unreachable")
        return

    tools.extend(mcp_tools)
    
    # Add custom date tools
    tools.append(get_datetime_context)
    tools.append(format_to_rfc3339)

    # Create agent
    agent = create_agent(
        model,
        tools,
    )

    user_input = input("Enter your prompt: ")
    while user_input.strip().lower() != 'q':
        response = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        print(response)
        user_input = input("Enter your prompt: ")


if __name__ == "__main__":
    asyncio.run(main())
