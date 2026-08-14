from dataclasses import dataclass

# ============================================================================
# Context of a bug
# ============================================================================
@dataclass
class FailureContext:
    command: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str

    def to_prompt(self) -> str:
        return (
            f"Command: {' '.join(self.command)}\n"
            f"Working directory: {self.cwd}\n"
            f"Exit code: {self.returncode}\n"
            f"\n--- stdout ---\n{self.stdout or '(empty)'}\n"
            f"\n--- stderr ---\n{self.stderr or '(empty)'}\n"
        )