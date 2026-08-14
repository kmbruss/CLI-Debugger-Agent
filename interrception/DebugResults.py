from dataclasses import dataclass

# ============================================================================
# Results of a successful debug
# ============================================================================
@dataclass
class DebugResults:
    answer: str
    turns: int
    stop_reason: str
    trajectory: list
    input_tokens: int
    output_tokens: int