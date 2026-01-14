#!/usr/bin/env python3
"""Check YouTrack tasks status"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient

def main():
    client = YouTrackClient()

    # Get all project issues
    print("📋 Fetching POD project tasks...\n")

    # Get tasks by state
    states = ["Open", "In Progress", "Review", "Done"]

    for state in states:
        issues = client.get_project_issues(state)
        if issues and not isinstance(issues, dict):  # dict means error
            print(f"\n🔹 **{state}** ({len(issues)}):")
            for issue in issues:
                summary = issue.get('summary', 'N/A')
                issue_id = issue.get('idReadable', 'N/A')
                print(f"  - {issue_id}: {summary}")
        elif state == "Open":
            print(f"\n🔹 **{state}**: No tasks")

    print("\n" + "="*60)

    # Get all issues regardless of state
    all_issues = client.get_project_issues()
    if all_issues and not isinstance(all_issues, dict):
        print(f"\n📊 **Total tasks in POD project**: {len(all_issues)}")

        # Count by state
        state_counts = {}
        for issue in all_issues:
            state_name = issue.get('state', {}).get('name', 'Unknown')
            state_counts[state_name] = state_counts.get(state_name, 0) + 1

        print("\n📈 **Breakdown by state**:")
        for state, count in sorted(state_counts.items()):
            print(f"  - {state}: {count}")

if __name__ == "__main__":
    main()
