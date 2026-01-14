#!/usr/bin/env python3
"""
PostToolUse Hook (Write): Auto-lint changed files
"""

import os
import sys
import json
import subprocess

def main():
    # Get hook input from stdin
    hook_input = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    
    # Extract file path from tool input
    tool_input = hook_input.get('tool_input', {})
    file_path = tool_input.get('file_path', '')
    
    if not file_path:
        return
    
    # Only lint Python files
    if not file_path.endswith('.py'):
        return
    
    feedback = []
    
    # Run ruff (fast linter)
    try:
        result = subprocess.run(
            ['ruff', 'check', file_path, '--fix', '--quiet'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            feedback.append(f"✓ Linted: {os.path.basename(file_path)}")
    except FileNotFoundError:
        # ruff not installed, try flake8
        try:
            result = subprocess.run(
                ['flake8', file_path, '--max-line-length=120', '--quiet'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.stdout:
                feedback.append(f"⚠ Lint issues in {os.path.basename(file_path)}")
        except:
            pass
    except:
        pass
    
    if feedback:
        print(json.dumps({"feedback": " | ".join(feedback)}))

if __name__ == "__main__":
    main()
