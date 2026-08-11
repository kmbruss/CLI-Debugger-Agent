# ============================================================================
# Imports
# ============================================================================
import os
import sys
import shlex
import subprocess

import anthropic
from dotenv import load_dotenv

from interrception.context import FailureContext

# ============================================================================
# Configuration
# ============================================================================
load_dotenv()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_KEY:
    print("Missing ANTHROPIC_API_KEY")
    sys.exit(1)
MAX_ATTEMPTS = 5


# ============================================================================
# Claude API Setup
# ============================================================================
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = (
    "You are a CLI debugging assistant. "
    "Respond in plain text only, not markdown "
    "Give simple, readable, yet informative output"
    "This is a one-shot tool — the user cannot respond or answer follow-up questions. "
    "Never ask the user a question or ask them to provide more information. "
    "If something is ambiguous, state your best-guess interpretation explicitly and proceed with it, "
    "or list the most likely possibilities as options rather than asking which one applies."
)

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the full contents of a file at the given path. Use this when you need to see code that isn't in the error message, such as a file mentioned in the traceback or one it imports from.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read."
                }
            },
            "required": ["path"]
        }
    }
]


# ============================================================================
# Helper Functions
# ============================================================================
def read_file(path: str) -> str:
    """Read file contents and return as string with error handling."""
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"\n Error: File not found at {path}\n"
    except Exception as e:
        return f"\n Error reading {path}: {e}\n"


def get_command() -> list[str]:
    """Get command to debug from args or shell history."""
    if len(sys.argv) > 1:
        return sys.argv[1:]

    # Fallback to reading from zsh history
    # ie. user command is just "interrception"
    with open(os.path.expanduser("~/.zsh_history"), "r", errors="ignore") as f:
        lines = f.readlines()

    if len(lines) < 2:
        print("\n   No previous command found in history\n")
        sys.exit(1)

    previous_command = lines[-2].strip()
    if previous_command.startswith("interrception"):
        print("\n   Last command was interrception - nothing new to debug\n")
        sys.exit(0)

    return shlex.split(previous_command)


# def validate_command(command: list[str]) -> None:
#     """Validate command target file exists if applicable."""
#     target = command[-1]
#     if ("." in target or "/" in target) and not os.path.isfile(target):
#         print(f"\n  File not found: {target}\n")
#         sys.exit(1)


def execute_command(command: list[str]) -> subprocess.CompletedProcess:
    """Execute command and return result."""
    try:
        return subprocess.run(command, capture_output=True, text=True, cwd=os.getcwd())
    except FileNotFoundError:
        print(f"\n  Command not found: {command[0]}\n")
        sys.exit(1)


def handle_tool_results(message) -> list[dict]:
    """Process tool use requests and return results."""
    tool_results = []
    for content in message.content:
        if content.type == "tool_use":
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": content.id,
                "content": read_file(content.input["path"])
            })
    return tool_results


def print_message_content(message) -> None:
    """Print text and tool use content from Claude's message."""
    for content in message.content:
        if content.type == "text":
            print(content.text)
        elif content.type == "tool_use":
            print(" Fetching Tool...")
            # print(f"    Tool use requested: {content.input}")


def debug_with_claude(error: str) -> None:
    """Main debugging loop using Claude API."""
    messages = [{"role": "user", "content": error}]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n  ---- Attempt {attempt} ----\n")

        message = client.messages.create(
            max_tokens=1000,
            messages=messages,
            model="claude-haiku-4-5",
            tools=TOOLS,
            system=SYSTEM_PROMPT
        )

        print_message_content(message)

        # Check if Claude needs to use tools
        if message.stop_reason != "tool_use":
            break

        # Process tool requests and add to conversation
        tool_results = handle_tool_results(message)
        messages.append({"role": "assistant", "content": message.content})
        messages.append({"role": "user", "content": tool_results})
    else:
        # Max attempts reached - get final response
        print("\n   Maximum attempts reached. Best guess:\n")
        final = client.messages.create(
            max_tokens=500,
            messages=messages,
            model="claude-haiku-4-5",
            system=SYSTEM_PROMPT
        )
        for content in final.content:
            if content.type == "text":
                print(content.text)


# ============================================================================
# Main Entry Point
# ============================================================================
def run():
    """Main function to run the CLI debugger."""
    command = get_command()
    # validate_command(command)
    result = execute_command(command)

    if result.returncode == 0:
        print("\n   No errors - clean run\n")
        return

    failure_context = FailureContext(
        command=command,
        cwd=os.getcwd(),
        returncode = result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )

    print(failure_context.to_prompt)
    debug_with_claude(failure_context.to_prompt())