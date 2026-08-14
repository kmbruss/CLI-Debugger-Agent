
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
            "Search file contents for a text pattern across a directory tree. Returns "
            "matching lines as 'path:line: content'. Use this FIRST when you need to "
            "find where something is defined (a class, function, or variable) and "
            "you don't already know which file it's in. Prefer this over guessing "
            "file paths with read_file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text to search for, e.g. 'class OutputCapturer' or 'def _format_timeframe'."
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
