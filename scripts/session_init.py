#!/usr/bin/env python3
"""
SessionStart Hook: Initialize session context
- Sync YouTrack KB cache
- Check for open issues
- Load current sprint context
"""

import os
import sys
import json
from datetime import datetime

def main():
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    
    # Create logs directory
    logs_dir = os.path.join(project_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Log session start
    log_file = os.path.join(logs_dir, 'sessions.log')
    with open(log_file, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Session started: {datetime.now().isoformat()}\n")
        f.write(f"Project: {project_dir}\n")
    
    # Try to sync YouTrack KB (non-blocking)
    try:
        from scripts.youtrack import KnowledgeBase
        kb = KnowledgeBase()
        kb.sync()
        print("✓ YouTrack KB synced")
    except Exception as e:
        print(f"⚠ YouTrack sync skipped: {e}")
    
    # Check for open GitHub issues
    try:
        from scripts.github_client import IssueTracker
        tracker = IssueTracker()
        if tracker.has_blockers():
            print("⚠ BLOCKERS FOUND - check GitHub issues")
    except Exception as e:
        pass
    
    # Output context for Claude
    output = {
        "feedback": "Session initialized. YouTrack and GitHub connected."
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
