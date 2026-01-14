#!/usr/bin/env python3
"""
Stop Hook: Auto-commit if tests passing and changes exist
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def has_changes():
    """Check if there are uncommitted changes"""
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True
    )
    return bool(result.stdout.strip())

def tests_passing():
    """Quick test check"""
    result = subprocess.run(
        ['pytest', 'tests/', '-x', '-q', '--tb=no'],
        capture_output=True,
        text=True,
        timeout=60
    )
    return result.returncode == 0

def get_changed_files():
    """Get list of changed files for commit message"""
    result = subprocess.run(
        ['git', 'diff', '--name-only', '--cached'],
        capture_output=True,
        text=True
    )
    if not result.stdout.strip():
        result = subprocess.run(
            ['git', 'diff', '--name-only'],
            capture_output=True,
            text=True
        )
    return result.stdout.strip().split('\n')[:5]

def main():
    # Check if auto-commit is enabled
    if os.environ.get('AUTO_COMMIT', 'true').lower() != 'true':
        return
    
    if not has_changes():
        return
    
    # Don't auto-commit if tests are failing
    try:
        if not tests_passing():
            print(json.dumps({"feedback": "⚠ Changes not committed - tests failing"}))
            return
    except Exception:
        # No tests or pytest not available - skip test check
        pass
    
    # Stage and commit
    try:
        subprocess.run(['git', 'add', '-A'], check=True)
        
        files = get_changed_files()
        timestamp = datetime.now().strftime('%H:%M')
        
        # Determine commit type from files
        if any('test' in f for f in files):
            commit_type = 'test'
        elif any(f.endswith('.md') for f in files):
            commit_type = 'docs'
        else:
            commit_type = 'wip'
        
        message = f"{commit_type}: auto-save {timestamp}\n\nFiles: {', '.join(files[:3])}"
        
        subprocess.run(['git', 'commit', '-m', message], check=True)
        
        print(json.dumps({"feedback": f"✓ Auto-committed: {commit_type}"}))
        
    except subprocess.CalledProcessError:
        pass

if __name__ == "__main__":
    main()
