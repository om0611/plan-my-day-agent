import contextlib
import json
from collections.abc import Generator
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def _parse_content_for_display(content: Any) -> Any:
    """
    Recursively parse JSON strings or FastMCP content structures
    so that embedded JSON strings are cleanly formatted.
    """
    if isinstance(content, str):
        with contextlib.suppress(Exception):
            parsed = json.loads(content)
            return _parse_content_for_display(parsed)
        return content

    if isinstance(content, list):
        # Handle FastMCP formatted text blocks like [{'type': 'text', 'text': '...'}]
        if (
            len(content) == 1
            and isinstance(content[0], dict)
            and content[0].get("type") == "text"
            and "text" in content[0]
        ):
            return _parse_content_for_display(content[0]["text"])
        return [_parse_content_for_display(item) for item in content]

    if isinstance(content, dict):
        return {k: _parse_content_for_display(v) for k, v in content.items()}

    return content


def display_welcome_banner() -> None:
    """Display the application welcome banner."""
    welcome_text = (
        "[bold cyan]🗓️  Plan My Day Agent[/bold cyan]\n"
        "[dim]Manage your schedule, check calendars, and plan activities.[/dim]\n"
        "[dim]Type [bold white]'q'[/bold white] or "
        "[bold white]'quit'[/bold white] to exit.[/dim]"
    )
    console.print(
        Panel.fit(
            welcome_text,
            border_style="cyan",
            padding=(1, 3),
        )
    )


def display_goodbye() -> None:
    """Display exit message."""
    console.print("[dim]Goodbye![/dim]")


def get_user_input(prompt: str = "👤 You: ") -> str | None:
    """Prompt the user for input with formatted prompt."""
    try:
        return console.input(f"\n[bold cyan]{prompt}[/bold cyan]").strip()
    except (KeyboardInterrupt, EOFError):
        return None


@contextlib.contextmanager
def thinking_status(
    message: str = "Agent is thinking...",
) -> Generator[None]:
    """Context manager to display a spinner while waiting for agent output."""
    with console.status(f"[bold cyan]{message}[/bold cyan]", spinner="dots"):
        yield


def display_tool_call(tool_name: str, args: Any) -> None:
    """Display a tool invocation with syntax-highlighted arguments."""
    parsed_args = _parse_content_for_display(args)

    if isinstance(parsed_args, (dict, list)):
        args_str = json.dumps(parsed_args, indent=2)
        renderable = Syntax(
            args_str,
            "json",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
    else:
        renderable = str(parsed_args)

    console.print(
        Panel(
            renderable,
            title=f"[bold yellow]🛠️  Tool Call:[/] [bold cyan]{tool_name}[/]",
            border_style="yellow",
            padding=(0, 1),
        )
    )


def display_tool_result(tool_name: str, content: Any) -> None:
    """Display a tool output result with smart formatting."""
    parsed_content = _parse_content_for_display(content)

    if isinstance(parsed_content, (dict, list)):
        content_str = json.dumps(parsed_content, indent=2)
        renderable = Syntax(
            content_str,
            "json",
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
    else:
        renderable = str(parsed_content)

    console.print(
        Panel(
            renderable,
            title=f"[bold blue]📥 Tool Result:[/] [bold cyan]{tool_name}[/]",
            border_style="blue",
            padding=(0, 1),
        )
    )


def display_agent_response(content: str) -> None:
    """Display the agent's final markdown response."""
    console.print(
        Panel(
            Markdown(content),
            title="[bold green]🤖 Day Planner Agent[/]",
            border_style="green",
            padding=(1, 2),
        )
    )


def display_thought(thought: str) -> None:
    """Display intermediate reasoning/thoughts."""
    if thought.strip():
        console.print(f"[dim italic]💭 Thinking: {thought.strip()}[/dim italic]\n")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green]✓[/green] {message}")


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]✗ {message}[/bold red]")
