from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from visualizer import (
    display_agent_response,
    display_error,
    display_thought,
    display_tool_call,
    display_tool_result,
    thinking_status,
)


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


def _process_ai_message(msg, tool_name_map: dict[str, str]) -> None:
    """Handle an AIMessage — either a thought + tool calls, or a final response."""
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


def _process_tool_message(msg, tool_name_map: dict[str, str]) -> None:
    """Handle a ToolMessage — display the tool's result."""
    call_id = getattr(msg, "tool_call_id", None)
    tool_name = getattr(msg, "name", None) or tool_name_map.get(call_id, "Tool")
    result_content = getattr(msg, "content", "")
    display_tool_result(tool_name, result_content)


def process_message(msg, tool_name_map: dict[str, str]) -> None:
    """Classify a single stream message and route it to the appropriate display."""
    if isinstance(msg, AIMessage) or hasattr(msg, "tool_calls"):
        _process_ai_message(msg, tool_name_map)
    elif isinstance(msg, ToolMessage) or msg.__class__.__name__ == "ToolMessage":
        _process_tool_message(msg, tool_name_map)


async def handle_stream(agent, user_input: str) -> None:
    """Stream agent responses for a single user turn, displaying output as it arrives."""
    tool_name_map: dict[str, str] = {}
    try:
        with thinking_status():
            async for chunk in agent.astream(
                {"messages": [{"role": "user", "content": user_input}]},
                stream_mode="updates",
            ):
                for _node_name, node_output in chunk.items():
                    messages = node_output.get("messages", [])
                    for msg in messages:
                        process_message(msg, tool_name_map)
    except Exception as e:
        display_error(f"Error during execution: {e}")
