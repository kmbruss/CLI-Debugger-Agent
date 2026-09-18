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
    MAX_LINES = 200  # Limit output to reduce token usage

    try:
        with open(path, "r", errors="ignore") as file:
            lines = file.readlines()

            begin = (start_line - 1) if start_line else 0
            end = end_line if end_line else len(lines)

            # Enforce max line limit
            requested_lines = end - begin
            if requested_lines > MAX_LINES:
                end = begin + MAX_LINES

            sliced = lines[begin:end]
            numbered = [
                f"{i}: {line.rstrip()}"
                for i, line in enumerate(sliced, start=begin + 1)
            ]

            body = "\n".join(numbered)
            result = f"Showing lines {begin + 1}-{end} of {len(lines)}:\n{body}"

            # Truncate if still too long
            if len(result) > 8000:
                result = result[:8000] + f"\n... (truncated, total file has {len(lines)} lines)"

            return result

    except FileNotFoundError:
        return f"\n Error: File not found at {path}\n"
    except Exception as e:
        return f"\n Error reading {path}: {e}\n"

    

    
IGNORE = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".mypy_cache", ".DS_Store"}
def list_directory(path: str = ".") -> str:
    MAX_FILES = 100  # Limit directory listings

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

        if len(file_list) >= MAX_FILES:
            break

    result = "\n".join(file_list) if file_list else "(empty)"
    if len(files) > MAX_FILES:
        result += f"\n... ({len(files)} total files, showing first {MAX_FILES})"

    return result


def grep(pattern: str, path: str = ".") -> str:
    MAX_MATCHES = 25  # Reduced from 100 to save tokens
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
                            # Early exit if we hit the limit
                            if len(matches) >= MAX_MATCHES * 2:
                                break
            except Exception:
                continue
            # Early exit at file level too
            if len(matches) >= MAX_MATCHES * 2:
                break
        if len(matches) >= MAX_MATCHES * 2:
            break

    if not matches:
        return f"No matches for '{pattern}' in {path}"
    if len(matches) > MAX_MATCHES:
        return "\n".join(matches[:MAX_MATCHES]) + f"\n... ({len(matches)} total matches, showing first {MAX_MATCHES})"
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
        # Remove all old cache_control markers from messages to avoid exceeding 4-block limit
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "cache_control" in item:
                        del item["cache_control"]

        # Add cache_control only to the last user message for conversation history caching
        # This keeps us within the 4-block limit: 1 for system + 1 for last message
        if len(messages) > 0 and messages[-1]["role"] == "user":
            content = messages[-1]["content"]
            if isinstance(content, str):
                messages[-1]["content"] = [
                    {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
                ]
            elif isinstance(content, list) and len(content) > 0:
                content[-1]["cache_control"] = {"type": "ephemeral"}

        message = client.messages.create(
            max_tokens=1000,
            messages=messages,
            model=model,
            tools=tools,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ]
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

    # Max attempts reached - prompt for final response
    # Add a message asking for the final diagnosis
    messages.append({
        "role": "user",
        "content": (
            "Investigation limit reached. Give your final diagnosis NOW in 3-6 sentences:\n"
            "PROBLEM: What's broken\n"
            "LOCATION: file:line\n"
            "FIX: What to change\n"
            "Be direct and concise. No tool requests allowed."
        )
    })

    # Remove all old cache_control markers
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "cache_control" in item:
                    del item["cache_control"]

    # Add cache_control to last message
    if len(messages) > 0 and messages[-1]["role"] == "user":
        content = messages[-1]["content"]
        if isinstance(content, str):
            messages[-1]["content"] = [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
            ]
        elif isinstance(content, list) and len(content) > 0:
            content[-1]["cache_control"] = {"type": "ephemeral"}

    final_attempt = client.messages.create(
        max_tokens=1000,  # Increased for detailed final answer
        messages=messages,
        model=model,
        tools=[],  # Explicitly disable tools for final response
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"}
            }
        ]
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