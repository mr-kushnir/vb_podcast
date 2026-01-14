#!/usr/bin/env python3
"""
PreToolUse Hook (Bash): Security gate before bash commands
- Block dangerous commands
- Warn about sensitive operations
"""

import os
import sys
import json
import re

BLOCKED_PATTERNS = [
    r'rm\s+-rf\s+/',          # rm -rf /
    r'rm\s+-rf\s+~',          # rm -rf ~
    r':\(\)\{\s*:\|:&\s*\};:', # Fork bomb
    r'mkfs\.',                 # Format disk
    r'dd\s+if=.+of=/dev/',    # Write to device
    r'>\s*/dev/sd',           # Overwrite disk
    r'chmod\s+-R\s+777\s+/',  # Dangerous permissions
]

WARN_PATTERNS = [
    (r'curl.*\|\s*bash', 'Piping curl to bash - verify source'),
    (r'wget.*\|\s*bash', 'Piping wget to bash - verify source'),
    (r'eval\s+', 'Using eval - ensure input is sanitized'),
    (r'exec\s+', 'Using exec - verify command'),
]

def main():
    hook_input = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    
    tool_input = hook_input.get('tool_input', {})
    command = tool_input.get('command', '')
    
    if not command:
        return
    
    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "block": True,
                "message": f"🚫 BLOCKED: Dangerous command detected"
            }
            print(json.dumps(output))
            return
    
    # Check warning patterns
    warnings = []
    for pattern, message in WARN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            warnings.append(message)
    
    if warnings:
        output = {
            "feedback": f"⚠ Security warning: {'; '.join(warnings)}"
        }
        print(json.dumps(output))

if __name__ == "__main__":
    main()
