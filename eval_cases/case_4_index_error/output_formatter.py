"""
Output formatter for case 4
"""

def format_results(results):
    """Format processing results for display"""
    formatted = []

    for i, result in enumerate(results):
        formatted.append(
            f"Array {i}: sum={result['sum']}, avg={result['average']:.2f}"
        )

    return "\n".join(formatted)
