from interrception.failure_context import FailureContext
from interrception.debug_agent import debug

from interrception.cli import client

import subprocess, os, sys

case = os.path.abspath("PySnooper")
cmd = ["python", "-m", "pytest", "tests/test_mini_toolbox.py", "-q"]

use_tools = "--no-tools" not in sys.argv

error_result = subprocess.run(cmd, capture_output=True, text=True, cwd=case)

failure_context = FailureContext(
    command=cmd, cwd=case, returncode=error_result.returncode,
    stdout=error_result.stdout, stderr=error_result.stderr
)

os.chdir(case)

debug_result = debug(
    failure_context.to_prompt(), 
    client, use_tools=use_tools
)

print(f"=== use_tools={use_tools} | turns={debug_result.turns} ===")
print(debug_result.answer)

for message in debug_result.trajectory:
        for block in message["content"]:
            if block.type == "tool_use":
                print(f"{block.name} ({block.input})")