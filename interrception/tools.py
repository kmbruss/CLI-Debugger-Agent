
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
        "description":
                "read a file's contents, optionally a line range (max 200 lines per call); "
                "ALWAYS specify a line range when you have a line number from grep - read ~50-100 lines around it; "
                "avoid reading entire files unless absolutely necessary for overall structure.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The path to the file to read."
                },
                "start_line": {
                    "type": "integer",
                    "description": "First line to read (1-indexed). Omit to read from the start."
                },
                "end_line": {
                    "type": "integer",
                    "description": "Last line to read, inclusive. Omit to read to the end."
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "list_directory",
        "description": (
            "List the files and subdirectories at a path. Directory names end with '/'. "
            "Use this when you need to discover what files exist before reading them, or "
            "to check whether a name refers to a module file or a package directory."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The directory to list. Defaults to current directory."
                }
            }
        }
    },
    {
        "name": "grep",
        "description": (
            "Search file contents for a text pattern across a directory tree (returns max 25 matches). "
            "Returns matching lines as 'path:line: content'. Use this FIRST when you need to "
            "find where something is defined (a class, function, or variable) and "
            "you don't already know which file it's in. Use specific patterns to avoid too many matches. "
            "Prefer this over guessing file paths with read_file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text to search for, e.g. 'class OutputCapturer' or 'def _format_timeframe'. Be specific."
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search. Defaults to the current directory."
                }
            },
            "required": ["pattern"]
        }
}
]
