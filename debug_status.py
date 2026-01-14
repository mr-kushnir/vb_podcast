#!/usr/bin/env python3
"""Debug YouTrack task status response"""

import sys
sys.path.insert(0, 'scripts')

from youtrack import YouTrackClient
import json

def main():
    client = YouTrackClient()

    print("🔍 Debugging POD-6 status response:\n")

    # Get POD-6 with all fields
    response = client._request(
        "GET",
        "/issues/POD-6?fields=id,idReadable,summary,customFields(name,value(name))"
    )

    print("Full response:")
    print(json.dumps(response, indent=2))

    print("\n" + "=" * 70)

    # Try to extract state
    if 'customFields' in response:
        print("\nCustom Fields:")
        for field in response['customFields']:
            name = field.get('name', 'N/A')
            value = field.get('value', {})
            if isinstance(value, dict):
                value_name = value.get('name', 'N/A')
            else:
                value_name = str(value)

            print(f"  {name}: {value_name}")

            if name == "State":
                print(f"\n✅ Found State field: {value_name}")

if __name__ == "__main__":
    main()
