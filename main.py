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

error = 'venv) kaanbruss@192 CLI-Debugger-Agent % python scratch/orders.py widgets: 7 left Traceback (most recent call last): File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/orders.py", line 14, in <module>fulfill(wh)File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/orders.py", line 10, in fulfillprocess_order(warehouse, pending_order)File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/orders.py", line 5, in process_orderremaining = warehouse.remove_stock(item, qty)File "/Users/kaanbruss/Portfolio/CLI-Debugger-Agent/scratch/inventory.py", line 6, in remove_stockself.stock[item] -= qtyKeyError: sprockets'

messages = [
    {"role": "user", "content": error}
]

message = client.messages.create(
    max_tokens=1000,
    messages=messages,
    model="claude-haiku-4-5",
    tools=tools
)

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

messages.append({"role": "assistant", "content": message.content})
messages.append({"role": "user", "content": tool_results})

message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=500,
    tools=tools,
    messages=messages
)

for content in message.content:
    if content.type == "text":
        print(content.text)