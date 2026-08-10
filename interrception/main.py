import os
import sys
import anthropic
import subprocess
import shlex
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def read_file(path: str) -> str:
    try:
        with open(path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return f"Error: File not found at {path}"
    except Exception as e:
        return f"Error reading {path}: {e}"


def run():
    if len(sys.argv) > 1:
        command = sys.argv[1:]
    else:
        with open(os.path.expanduser("~/.zsh_history"), "r", errors="ignore") as f:
            lines = f.readlines()

        if len(lines) < 2:
            print("No previous command found in history")
            sys.exit(1)

        
        previous_command = lines[-2].strip()
        if previous_command.startswith("interrception"):
            print("Last command was interrception - nothing new to debug")
            sys.exit(1)
        command = shlex.split(previous_command)

    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        sys.exit(1)

    if result.returncode == 0:
        print("No errors - clean run")
        return
    error = result.stderr
    
    messages = [{"role": "user", "content": error}]

    breakloop = 0

    while True:

        breakloop += 1
        if breakloop > 5:
            print("Maximum attempts reached. Best guess:")
            final = client.messages.create(
                max_tokens=500,
                messages=messages,
                model="claude-haiku-4-5",
                system=system
            )
            for content in final.content:
                if content.type == "text":
                    print(content.text)
            break

        print(f"---- Attempt {breakloop} ----")

        message = client.messages.create(
            max_tokens=1000,
            messages=messages,
            model="claude-haiku-4-5",
            tools=tools,
            system=system
        )

        for content in message.content:
            if content.type == "text":
                print(content.text)
            elif content.type == "tool_use":
                print(f"Tool use requested: {content.input}")

        tool_results = []
        for content in message.content:
            if content.type == "tool_use":
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": content.id,
                        "content": read_file(content.input["path"])
                    }
                )

        if message.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": message.content})
        messages.append({"role": "user", "content": tool_results})


tools = [
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

system = "You are a CLI debugging assistant. " \
         "Respond in plain text only, not markdown " \
         "Give simple, readable, yet informative output"
