#!/usr/bin/env python3
"""
PostToolUse Hook (Bash *test*): Watch test results
- Log test outcomes
- Update YouTrack blockers if failures
"""

import os
import sys
import json
from datetime import datetime

def main():
    hook_input = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    
    tool_output = hook_input.get('tool_output', {})
    stdout = tool_output.get('stdout', '')
    stderr = tool_output.get('stderr', '')
    returncode = tool_output.get('returncode', 0)
    
    # Parse test results
    output_text = stdout + stderr
    
    passed = output_text.count(' passed')
    failed = output_text.count(' failed')
    errors = output_text.count(' error')
    
    # Log results
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    log_file = os.path.join(project_dir, 'logs', 'tests.log')
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, 'a') as f:
        f.write(f"{datetime.now().isoformat()} | Pass: {passed} | Fail: {failed} | Errors: {errors}\n")
    
    # Provide feedback
    if failed > 0 or errors > 0:
        feedback = f"❌ Tests: {passed} passed, {failed} failed, {errors} errors"
    elif passed > 0:
        feedback = f"✅ Tests: {passed} passed"
    else:
        feedback = None
    
    if feedback:
        print(json.dumps({"feedback": feedback}))

if __name__ == "__main__":
    main()
