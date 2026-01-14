#!/usr/bin/env python3
"""List all POD project tasks with details"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient

def main():
    client = YouTrackClient()

    print("📋 All POD project tasks:\n")

    # Get all issues
    all_issues = client.get_project_issues()

    if all_issues and not isinstance(all_issues, dict):
        for issue in all_issues:
            issue_id = issue.get('idReadable', 'N/A')
            summary = issue.get('summary', 'N/A')
            state = issue.get('state', {}).get('name', 'Unknown')

            print(f"{issue_id}: {summary}")
            print(f"  State: {state}")

            # Get full details
            details = client.get_issue(issue_id)
            if details and not isinstance(details, dict) or 'error' not in details:
                desc = details.get('description', 'N/A')
                if desc and desc != 'N/A':
                    # Show first 100 chars of description
                    desc_preview = desc[:100].replace('\n', ' ')
                    print(f"  Description: {desc_preview}...")
            print()

    else:
        print("Error fetching tasks or no tasks found")

if __name__ == "__main__":
    main()
