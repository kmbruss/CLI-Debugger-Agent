from dataclasses import dataclass

# ============================================================================
# Setup
# ============================================================================
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
# Results of a successful debug
# ============================================================================
@dataclass
class DebugResults:
    answer: str
    turns: int
    stop_reason: str
    trajectory: list


# ============================================================================
# Functions
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


# ============================================================================
# agent loop
# ============================================================================
def debug(prompt: str, client, model: str = "claude-haiku-4-5", max_attempts: int = 5, use_tools: bool = True) -> DebugResults:
    """Run the agent loop against a failure prompt. No printing -> returns a DebugResult."""
    messages = [{"role": "user", "content": prompt}]
    trajectory = []

    tools = TOOLS if use_tools else []

    for attempt in range(1, max_attempts + 1):
        message = client.messages.create(
            max_tokens=1000,
            messages=messages,
            model=model,
            tools=tools,
            system=SYSTEM_PROMPT
        )

        trajectory.append({
            "attempt": attempt,
            "stop_reason": message.stop_reason,
            "content": message.content
        })

        # Check if Claude needs to use tools
        if message.stop_reason != "tool_use":
            answer = next((content.text for content in message.content if content.type == "text"), "")
            return DebugResults(answer=answer, turns=attempt, stop_reason="answered", trajectory=trajectory)

        # Process tool requests and add to conversation
        tool_results = handle_tool_results(message)
        messages.append({"role": "assistant", "content": message.content})
        messages.append({"role": "user", "content": tool_results})
    
    # Max attempts reached - get final response
    final_attempt = client.messages.create(
        max_tokens=500,
        messages=messages,
        model=model,
        system=SYSTEM_PROMPT
    )

    trajectory.append({
            "attempt": max_attempts + 1,
            "stop_reason": "max_attempts",
            "content": final_attempt.content
        })
    
    answer = next((content.text for content in final_attempt.content if content.type == "text"), "")

    return DebugResults(
        answer=answer, 
        turns=max_attempts, 
        stop_reason="max_attempts",
        trajectory=trajectory
    )