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
for idx, CASE in enumerate(CASES, 1):
    print(f"\n{'='*80}")
    print(f"CASE {idx}/{len(CASES)}: {CASE['id']}")
    print(f"{'='*80}")
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
            print(f"\n⚠️  SKIPPED: Revert failed")
            print(f"   Error: {bad_repo_result.stderr.strip()}")
            continue

        error_result = subprocess.run(
            cmd, capture_output=True,
            text=True, cwd=repo
        )

        if error_result.returncode == 0:
            print(f"\n⚠️  SKIPPED: Command succeeded (expected failure)")
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

        # Format output nicely
        print(f"\n{'='*80}")
        print(f"METRICS:")
        print(f"  Turns:         {debug_result.turns}")
        print(f"  Input tokens:  {debug_result.input_tokens:,}")
        print(f"  Output tokens: {debug_result.output_tokens:,}")
        print(f"  Total tokens:  {debug_result.input_tokens + debug_result.output_tokens:,}")
        print(f"  Stop reason:   {debug_result.stop_reason}")

        # Tool calls
        tool_calls = [
            block for message in debug_result.trajectory
            for block in message["content"]
            if block.type == "tool_use"
        ]

        if tool_calls:
            print(f"\nTOOL CALLS ({len(tool_calls)} total):")
            for i, block in enumerate(tool_calls, 1):
                if block.name == "read_file":
                    path = block.input.get("path", "").replace(repo + "/", "")
                    start = block.input.get("start_line")
                    end = block.input.get("end_line")
                    if start and end:
                        print(f"  {i}. read_file: {path} (lines {start}-{end})")
                    else:
                        print(f"  {i}. read_file: {path}")
                elif block.name == "grep":
                    pattern = block.input.get("pattern", "")
                    print(f"  {i}. grep: '{pattern}'")
                elif block.name == "list_directory":
                    path = block.input.get("path", ".").replace(repo + "/", "")
                    print(f"  {i}. list_directory: {path}")
                else:
                    print(f"  {i}. {block.name}: {block.input}")

        print(f"\nANSWER:")
        # Truncate long answers for readability
        answer_lines = debug_result.answer.split('\n')
        if len(answer_lines) > 30:
            print('\n'.join(answer_lines[:30]))
            print(f"\n  ... ({len(answer_lines) - 30} more lines)")
        else:
            print(debug_result.answer)
        print(f"{'='*80}\n")

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

# Print summary table
if results:
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"{'Case ID':<30} {'Turns':<8} {'Input':<12} {'Output':<12} {'Total':<12} {'Stop':<15}")
    print("-"*100)
    for r in results:
        total = r['input_tokens'] + r['output_tokens']
        print(f"{r['case_id']:<30} {r['turns']:<8} {r['input_tokens']:<12,} {r['output_tokens']:<12,} {total:<12,} {r['stop_reason']:<15}")

    total_input = sum(r['input_tokens'] for r in results)
    total_output = sum(r['output_tokens'] for r in results)
    total_all = total_input + total_output
    print("-"*100)
    print(f"{'TOTAL':<30} {'':<8} {total_input:<12,} {total_output:<12,} {total_all:<12,}")
    print("="*100 + "\n")

#  Save results if requested
if should_save:
    save_results(results, use_tools)

