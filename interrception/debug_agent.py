from interrception.DebugResults import DebugResults

from interrception.tools import TOOLS
from interrception.tools import SYSTEM_PROMPT

import os

# ============================================================================
# Functions
# ============================================================================
def choose_tool(block) -> str:
    tool = TOOLS_AVAILABLE.get(block.name)
    if tool is None:
        return f"Tool unknown '{block.name}'"   
    try:
        # Unload block (path (and pattern for grep) into chosen tool)
        return tool(**block.input)
    except Exception as e:
        return f"Error running {block.name}: {type(e).__name__}: {e}"


def read_file(path: str, start_line: int = None, end_line: int = None) -> str:
    """Read file contents and return as string with error handling."""
    try:
        with open(path, "r", errors="ignore") as file:
            lines = file.readlines()

            begin = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)

            sliced = lines[begin:end]
            numbered = [
                f"{i}: {line.rstrip()}"
                for i, line in enumerate(sliced, start=begin + 1)
            ]

            body = "\n".join(numbered)
            return f"Showing lines {begin + 1}-{end} of {len(lines)}:\n{body}"
        
    except FileNotFoundError:
        return f"\n Error: File not found at {path}\n"
    except Exception as e:
        return f"\n Error reading {path}: {e}\n"

    

    
IGNORE = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".mypy_cache", ".DS_Store"}
def list_directory(path: str = ".") -> str:
    try:
        files = sorted(os.listdir(path))
    except Exception as e:
        return f"error listing {path}: {e}"

    file_list = []
    for f in files:
        if f in IGNORE:
            continue
        full_path = os.path.join(path, f)
        file_list.append(f"{f}/" if os.path.isdir(full_path) else f)

    return "\n".join(file_list) if file_list else "(empty)"


def grep(pattern: str, path: str = ".") -> str:
    matches = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [
            d for d in dirnames 
            if d not in IGNORE
            and not d.startswith(".")
            and not d.startswith("venv")
        ]
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                with open(filepath, "r", errors="ignore") as contents:
                    for line_no, line in enumerate(contents, 1):
                        if pattern in line:
                            matches.append(f"{filepath}:{line_no}: {line.strip()}")
            except Exception:
                continue
    if not matches:
        return f"No matches for '{pattern}' in {path}"
    if (len(matches) > 100):
        return "\n".join(matches[:100]) + f"\n... ({len(matches)} total matches, showing first 100)"
    return "\n".join(matches)


TOOLS_AVAILABLE = {
    "read_file": read_file,
    "list_directory": list_directory,
    "grep": grep,
}


def handle_tool_results(message, seen_reads:set) -> list[dict]:
    """Process tool use requests and return results."""
    tool_results = []

    for block in message.content:
        if block.type == "tool_use":
            if block.name == "read_file":
                path = os.path.abspath(block.input["path"])
                key = (path, block.input.get("start_line"), block.input.get("end_line"))
                if key in seen_reads:
                    content = (
                        f"[Already read the exact range of {path} earlier in this conversation. "
                        f"Its contents are above, scroll up rather than re-reading.]"
                    )
                else:
                    seen_reads.add(key)
                    content = choose_tool(block)
            else:
                content = choose_tool(block)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content
            })
    return tool_results


# ============================================================================
# agent loop
# ============================================================================
def debug(prompt: str, client, model: str = "claude-haiku-4-5", max_attempts: int = 5, use_tools: bool = True) -> DebugResults:
    """Run the agent loop against a failure prompt. No printing -> returns a DebugResult."""
    messages = [{"role": "user", "content": prompt}]
    trajectory = []
    seen_paths = set()
    total_input_tokens = 0
    total_output_tokens = 0

    tools = TOOLS if use_tools else []

    for attempt in range(1, max_attempts + 1):
        message = client.messages.create(
            max_tokens=1000,
            messages=messages,
            model=model,
            tools=tools,
            system=SYSTEM_PROMPT
        )

        # Track token usage
        total_input_tokens += message.usage.input_tokens
        total_output_tokens += message.usage.output_tokens

        trajectory.append({
            "attempt": attempt,
            "stop_reason": message.stop_reason,
            "content": message.content
        })

        # Check if Claude needs to use tools
        if message.stop_reason != "tool_use":
            answer = next((content.text for content in message.content if content.type == "text"), "")
            return DebugResults(
                answer=answer,
                turns=attempt,
                stop_reason="answered",
                trajectory=trajectory,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens
            )

        # Process tool requests and add to conversation
        tool_results = handle_tool_results(message, seen_paths)
        messages.append({"role": "assistant", "content": message.content})
        messages.append({"role": "user", "content": tool_results})

    # Max attempts reached - get final response
    final_attempt = client.messages.create(
        max_tokens=500,
        messages=messages,
        model=model,
        system=SYSTEM_PROMPT
    )

    # Track final token usage
    total_input_tokens += final_attempt.usage.input_tokens
    total_output_tokens += final_attempt.usage.output_tokens

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
        trajectory=trajectory,
        input_tokens=total_input_tokens,
        output_tokens=total_output_tokens
    )