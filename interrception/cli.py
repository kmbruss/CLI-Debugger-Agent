import os
import sys
import shlex
import subprocess

import anthropic
from dotenv import load_dotenv

from interrception.failure_context import FailureContext
from interrception.debug_agent import debug

# ============================================================================
# Configuration
# ============================================================================
load_dotenv()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

if not ANTHROPIC_KEY:
    print("Missing ANTHROPIC_API_KEY")
    sys.exit(1)

MAX_ATTEMPTS = 5

# client
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ============================================================================
# Functions
# ============================================================================
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


def execute_command(command: list[str]) -> subprocess.CompletedProcess:
    """Execute command and return result."""
    try:
        return subprocess.run(command, capture_output=True, text=True, cwd=os.getcwd(), timeout=10)
    except subprocess.TimeoutExpired:
        print(f"\n '{' '.join(command)}' didn't finish in 10s - likely waiting on input, not a crash\n")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n  Command not found: {command[0]}\n")
        sys.exit(1)


# ============================================================================
# Main Entry Point
# ============================================================================
def run():
    """Main entry point for CLI"""
    command = get_command()
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

    print("\n   ---- Debugging ----\n")
    debug_result = debug(
        prompt=failure_context.to_prompt(), 
        client=client,
        max_attempts=MAX_ATTEMPTS
    )
    print(debug_result.answer)

