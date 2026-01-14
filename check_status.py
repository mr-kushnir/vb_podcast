#!/usr/bin/env python3
"""Check status of each POD task individually"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient

def main():
    client = YouTrackClient()

    task_ids = ["POD-1", "POD-2", "POD-3", "POD-4", "POD-5", "POD-6"]

    print("📊 POD Project Status:\n")
    print("=" * 70)

    completed = []
    pending = []

    for task_id in task_ids:
        details = client.get_issue(task_id)

        if details and 'error' not in details:
            summary = details.get('summary', 'N/A')
            state = details.get('state', {}).get('name', 'Unknown')

            # Check if done
            is_done = state.lower() in ['done', 'closed', 'resolved', 'fixed']

            status_icon = "✅" if is_done else "⏳"
            print(f"{status_icon} {task_id}: {summary}")
            print(f"   State: {state}")

            if is_done:
                completed.append(task_id)
            else:
                pending.append(task_id)

        print()

    print("=" * 70)
    print(f"\n✅ Completed: {len(completed)}/{len(task_ids)}")
    if completed:
        print(f"   {', '.join(completed)}")

    if pending:
        print(f"\n⏳ Pending: {len(pending)}")
        print(f"   {', '.join(pending)}")
    else:
        print(f"\n🎉 All technical tasks completed!")

if __name__ == "__main__":
    main()
