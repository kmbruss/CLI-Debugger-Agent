from interrception.FailureContext import FailureContext
from interrception.debug_agent import debug
from interrception.cli import client

import subprocess, os, sys, json

# Test cases containing repo info, commits, and commands that should fail after reverting changes
CASES = [
    {
        "id": "pysnooper_outputcapturer",
        "repo": "repos/PySnooper",
        "commit": "a602866",
        "revert_path": "tests/mini_toolbox/__init__.py",
        "cmd": ["python", "-m", "pytest", "tests/test_mini_toolbox.py", "-q"],
    },   
    {
        "id": "arrow_humanize_float", 
        "repo": "repos/arrow", 
        "commit": "b8a9df7",
        "revert_path": "arrow/",
        "cmd": ["python","-m","pytest","tests/test_arrow.py","-q","--no-cov","-k","no_floats"]
    },
    {
        "id": "arrow_tzinfo_kwarg", 
        "repo": "repos/arrow", 
        "commit": "06fe693",
        "revert_path": "arrow/",
        "cmd": ["python","-m","pytest","tests/test_factory.py","-q","--no-cov","-k","tzinfo_kwarg"]
    },
    {
        "id": "arrow_empty_granularity", 
        "repo": "repos/arrow", 
        "commit": "cc1cbeb",
        "revert_path": "arrow/",
        "cmd": ["python","-m","pytest","tests/test_arrow.py","-q","--no-cov","-k","empty_granularity"]
    },
    {
        "id": "click_write_usage", 
        "repo": "repos/click", 
        "commit": "0551bf5",
        "revert_path": "src/click/",
        "cmd": ["python","-m","pytest","tests/test_formatting.py","-q","-k","write_usage"]
    },
]

use_tools = "--no-tools" not in sys.argv
should_save = "--save" in sys.argv
results = []


def save_results(results, use_tools):
    os.makedirs("results", exist_ok=True)
    arm = "with_tools" if use_tools else "no_tools"
    # path = f"results/{arm}.json"
    path = "results/with_tools_grep_fullread.json"

    with open(path, "w") as f:
         json.dump(results, f, indent=2)

    print(f"\nSaved {len(results)} results to {path}")

# Helper function to run git commands in a specific repository
def git(repo, *args, input=None):
     return subprocess.run(
        ["git", *args], cwd=repo,
        capture_output=True, text=True, input=input
    )


# iterate through cases 
for CASE in CASES:
    print(f" ----- {CASE["id"]} -----")
    original = os.getcwd()

    repo = os.path.abspath(CASE["repo"])
    commit = CASE["commit"]
    cmd = CASE["cmd"]
    revert_path = CASE["revert_path"]

    try:
        # Checkout the specific commit
        git(repo, "checkout", "-q", commit)

        # Get the diff that was introduced in this commit
        diff = git(repo, "show", commit, "--", revert_path).stdout

        # Apply the diff in reverse to revert the fix and introduce the bug
        bad_repo_result = git(repo, "apply", "-R", "-", input=diff)

        if bad_repo_result.returncode != 0:
            print(f"REVERT FAILED for {CASE['id']}: {bad_repo_result.stderr.strip()}")
            continue

        error_result = subprocess.run(
            cmd, capture_output=True, 
            text=True, cwd=repo
        )

        if error_result.returncode == 0:
            print(f"{CASE['id']} exited code 0")
            continue

        failure_context = FailureContext(
            command=cmd, cwd=repo, returncode=error_result.returncode,
            stdout=error_result.stdout, stderr=error_result.stderr
        )

        os.chdir(repo)

        debug_result = debug(
            failure_context.to_prompt(),
            client, use_tools=use_tools
        )

        print(f"=== use_tools={use_tools} | turns={debug_result.turns} | tokens: {debug_result.input_tokens} in / {debug_result.output_tokens} out ===")
        print(debug_result.answer)

        for message in debug_result.trajectory:
                for block in message["content"]:
                    if block.type == "tool_use":
                        print(f"{block.name} ({block.input})")

        results.append({
            "case_id": CASE["id"],
            "answer": debug_result.answer,
            "turns":debug_result.turns,
            "stop_reason": debug_result.stop_reason,
            "input_tokens": debug_result.input_tokens,
            "output_tokens": debug_result.output_tokens,
            "tool_calls": [
                {"tool": block.name, "input": block.input}
                for turn in debug_result.trajectory
                    for block in turn["content"]
                        if block.type == "tool_use"
            ]
        })

    finally:
        os.chdir(original)
        git(repo, "checkout", "-q", "--", ".")
        if git(repo, "checkout", "-q", "master").returncode != 0:
             git(repo, "checkout", "-q", "main")

#  Save results if requested
if should_save:
    save_results(results, use_tools)

