import asyncio
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.agent import Agent

console = Console()


def main():
    load_dotenv()

    console.print(
        Panel.fit(
            "[bold]OpenBridge[/bold] — Self-Extending Agent\n"
            "[dim]Find any API. Deploy as MCP. Gain new capabilities.[/dim]",
            border_style="bright_cyan",
        )
    )

    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        console.print("\n[bold]What would you like to integrate?[/bold]")
        user_input = console.input("[bright_cyan]> [/bright_cyan]")

    if not user_input.strip():
        console.print("[red]No input provided.[/red]")
        sys.exit(1)

    agent = Agent()
    asyncio.run(agent.run(user_input))


if __name__ == "__main__":
    main()
