# interrception

An AI-powered CLI debugging agent.

Most LLM error tools take an error and take a guess at what the fix could be based off just the text. This works for shallow projects, but not for errors that don't give exact locations of errors. `interrception` gives the model tools to actually read your code, so instead of pattern-matching on the error, it explores the repo, follows imports, and finds the real root cause, which is often in a file the traceback never mentions.

## Usage

```bash
# wrap a command
interrception python app.py

# or run it bare, right after something fails
python app.py
interrception
```

## How it works

The failing command's exit code, stdout, and stderr are packaged into a prompt and handed to an agent loop with tool access. The model can call:

- `read_file` -> read a file, optionally a line range
- `grep` -> search the codebase for a pattern
- `list_directory` -> allow directory navigation

For each turn, the model decides what it needs next, and the loop feeds results back and repeats until it has an answer or hits a turn cap.

## Notes

- Requires `ANTHROPIC_API_KEY` in a `.env` file.

## Install

```bash
pip install -e .
```