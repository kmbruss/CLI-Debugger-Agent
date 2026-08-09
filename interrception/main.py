import os
import anthropic
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

error = 'widgets: 7 left\nTraceback (most recent call last):\n  File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/scratch_main.py", line 6, in <module>\n    fulfill(wh)\n  File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/orders.py", line 11, in fulfill\n    process_order(warehouse, pending_order)\n  File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/orders.py", line 6, in process_order\n    remaining = warehouse.remove_stock(item, qty)\n  File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/inventory.py", line 6, in remove_stock\n    self.stock[item] -= qty\nKeyError: \'sprockets\''
messages = [
    {"role": "user", "content": error}
]

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