"""
Reporting module for case 5
"""

def generate_report(users):
    """Generate a report from user data"""
    report_lines = ["User Report", "=" * 40]

    for user in users:
        report_lines.append(f"- {user.name} (ID: {user.id})")

    report_lines.append("=" * 40)
    report_lines.append(f"Total users: {len(users)}")

    return "\n".join(report_lines)
