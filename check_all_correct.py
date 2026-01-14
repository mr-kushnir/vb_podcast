#!/usr/bin/env python3
"""Check all POD tasks with correct API format"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient

def get_task_state(client, task_id):
    """Get task state from customFields"""
    response = client._request(
        "GET",
        f"/issues/{task_id}?fields=id,idReadable,summary,customFields(name,value(name))"
    )

    if response and 'customFields' in response:
        for field in response['customFields']:
            if field.get('name') == 'State' and field.get('value'):
                return field['value'].get('name', 'Unknown')

    return 'Unknown'

def main():
    client = YouTrackClient()

    task_ids = ["POD-1", "POD-2", "POD-3", "POD-4", "POD-5", "POD-6"]

    print("📊 POD Project Status Report:\n")
    print("=" * 70)

    completed = []
    in_progress = []
    open_tasks = []

    for task_id in task_ids:
        response = client._request(
            "GET",
            f"/issues/{task_id}?fields=id,idReadable,summary,customFields(name,value(name))"
        )

        if response and 'error' not in response:
            summary = response.get('summary', 'N/A')
            state = 'Unknown'

            # Extract state from customFields
            if 'customFields' in response:
                for field in response['customFields']:
                    if field.get('name') == 'State' and field.get('value'):
                        state = field['value'].get('name', 'Unknown')
                        break

            # Categorize
            if state.lower() in ['done', 'closed', 'resolved', 'fixed']:
                status_icon = "✅"
                completed.append(task_id)
            elif state.lower() in ['in progress', 'in-progress']:
                status_icon = "🔄"
                in_progress.append(task_id)
            elif state.lower() in ['open', 'to do', 'todo']:
                status_icon = "📋"
                open_tasks.append(task_id)
            else:
                status_icon = "❓"
                open_tasks.append(task_id)

            print(f"{status_icon} {task_id}: {summary}")
            print(f"   State: {state}")
            print()

    print("=" * 70)
    print(f"\n📈 Summary:")
    print(f"   ✅ Completed: {len(completed)}/{len(task_ids)}")
    if completed:
        print(f"      {', '.join(completed)}")

    if in_progress:
        print(f"   🔄 In Progress: {len(in_progress)}")
        print(f"      {', '.join(in_progress)}")

    if open_tasks:
        print(f"   📋 Open/Pending: {len(open_tasks)}")
        print(f"      {', '.join(open_tasks)}")

    if len(completed) == len([t for t in task_ids if t != "POD-1"]):
        print(f"\n🎉 All technical tasks (POD-2 to POD-6) completed!")
        print(f"   POD-1 is project description (not a task)")

if __name__ == "__main__":
    main()
