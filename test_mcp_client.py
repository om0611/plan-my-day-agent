import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient  
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

load_dotenv()

async def main():
    client = MultiServerMCPClient(
        {
            "math": {
                "transport": "stdio",
                "command": "uv",
                "args": ["run", "test_mcp_server.py"],
            },
        }
    )

    model = ChatOllama(
        model="gemma4:31b-cloud",
        base_url="https://ollama.com",
        temperature=0,
    )

    tools = await client.get_tools()
    agent = create_agent(
        model,
        tools,
    )
    math_response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "what's (3 + 5) x 12?"}]}
    )
    print(math_response)

if __name__ == "__main__":
    asyncio.run(main())