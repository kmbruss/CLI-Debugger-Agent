import os
import sys
import subprocess

from interrception.debug_agent import debug
from interrception.failure_context import FailureContext

from interrception.cli import client

CASES_DIR = "eval_cases/"

def files_read(trajectory) -> list[str]:
    paths =[]
    for message in trajectory:
        for block in message["content"]:
            if block.type == "tool_use":
                paths.append(block.input["path"])

    return paths

def run_cases(cases_dir: str) -> list[dict]:
    results = []
    for case_folder in sorted(os.listdir(cases_dir)):

        case_path = "eval_cases/case_1_import_error/"#os.path.join(cases_dir, case_folder)
        # main_file = os.path.join(case_path, "main.py")

        result = subprocess.run(
            ["python", "main.py"], 
            capture_output=True, text=True, cwd=case_path, timeout=30
        )

        if result.returncode == 0:
            print(f"folder is somehow fixed: {case_folder}")
            continue

        failure_context = FailureContext(
            command=["python", "main.py"],
            cwd=case_path,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )

        original = os.getcwd()
        try:
            os.chdir(case_path)
            debug_results = debug(prompt=failure_context.to_prompt(), client=client)
        finally:
            os.chdir(original)

        results.append({
            "id": case_folder,
            "answer": debug_results.answer,
            "turns": debug_results.turns,
            "stop_reason": debug_results.stop_reason,
            "trajectory": files_read(debug_results.trajectory)
        })

    return results

def run():
    results = run_cases(CASES_DIR)
    for r in results:
        print(f"\n--- {r['id']} ---")
        print(f"    turns: {r['turns']}  stop_reason: {r['stop_reason']}")
        print(f"    files read: {r['trajectory']}")
        print(f"    {r['answer'][:400]}")



if __name__ == "__main__":
    run()