#!/usr/bin/env python3
"""
GitHub API Client
Handles Issues, Commits, Pull Requests
"""

import os
import json
import subprocess
import requests
from typing import Optional, List, Dict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.repo = os.getenv("GITHUB_REPO", "")
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.api_base = "https://api.github.com"
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request to GitHub"""
        url = f"{self.api_base}{endpoint}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            print(f"GitHub API Error: {e}")
            return {"error": str(e)}

    # ==================== ISSUES ====================
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> dict:
        """Create GitHub issue"""
        data = {
            "title": title,
            "body": body,
            "labels": labels or []
        }
        return self._request("POST", f"/repos/{self.repo}/issues", data)
    
    def get_issues(self, state: str = "open", labels: str = None) -> List[dict]:
        """Get issues"""
        endpoint = f"/repos/{self.repo}/issues?state={state}"
        if labels:
            endpoint += f"&labels={labels}"
        return self._request("GET", endpoint)
    
    def get_issue(self, issue_number: int) -> dict:
        """Get single issue"""
        return self._request("GET", f"/repos/{self.repo}/issues/{issue_number}")
    
    def update_issue(self, issue_number: int, state: str = None, body: str = None) -> dict:
        """Update issue"""
        data = {}
        if state:
            data["state"] = state
        if body:
            data["body"] = body
        return self._request("PATCH", f"/repos/{self.repo}/issues/{issue_number}", data)
    
    def close_issue(self, issue_number: int, comment: str = None) -> dict:
        """Close issue with optional comment"""
        if comment:
            self.add_comment(issue_number, comment)
        return self.update_issue(issue_number, state="closed")
    
    def add_comment(self, issue_number: int, body: str) -> dict:
        """Add comment to issue"""
        data = {"body": body}
        return self._request("POST", f"/repos/{self.repo}/issues/{issue_number}/comments", data)
    
    def create_bug_issue(self, scenario: str, expected: str, actual: str, 
                         test_file: str, priority: str = "Medium") -> dict:
        """Create formatted bug issue"""
        body = f"""## Bug Report

**BDD Scenario**: {scenario}

**Expected Behavior**: 
{expected}

**Actual Behavior**: 
{actual}

**Test File**: `{test_file}`

**Priority**: {priority}

**Steps to Reproduce**:
1. Run the test
2. Observe failure

---
*Created by TESTER agent*
"""
        labels = ["bug", f"priority:{priority.lower()}"]
        return self.create_issue(f"Bug: {scenario[:50]}", body, labels)
    
    def create_security_issue(self, vuln_type: str, severity: str, location: str,
                              description: str, recommendation: str, cwe: str = None) -> dict:
        """Create formatted security issue"""
        body = f"""## Security Vulnerability

**Type**: {vuln_type}
**Severity**: {severity}
**CWE**: {cwe or 'N/A'}

**Location**: `{location}`

**Description**:
{description}

**Recommendation**:
{recommendation}

**References**:
- [OWASP](https://owasp.org)
- [CWE Database](https://cwe.mitre.org)

---
*Created by SECURITY agent*
"""
        labels = ["security", f"severity:{severity.lower()}"]
        return self.create_issue(f"Security: {vuln_type}", body, labels)

    # ==================== GIT OPERATIONS ====================
    
    def git_commit(self, message: str, files: List[str] = None) -> bool:
        """Stage and commit files"""
        try:
            if files:
                for f in files:
                    subprocess.run(["git", "add", f], check=True)
            else:
                subprocess.run(["git", "add", "-A"], check=True)
            
            subprocess.run(["git", "commit", "-m", message], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git commit error: {e}")
            return False
    
    def git_push(self, branch: str = None) -> bool:
        """Push to remote"""
        try:
            cmd = ["git", "push"]
            if branch:
                cmd.extend(["-u", "origin", branch])
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Git push error: {e}")
            return False
    
    def create_conventional_commit(self, commit_type: str, scope: str, subject: str,
                                   body: str = None, issue_refs: List[str] = None,
                                   youtrack_refs: List[str] = None) -> bool:
        """Create conventional commit message and commit"""
        message = f"{commit_type}({scope}): {subject}"
        
        if body:
            message += f"\n\n{body}"
        
        footer = []
        if issue_refs:
            footer.append(f"Closes {', '.join(f'#{i}' for i in issue_refs)}")
        if youtrack_refs:
            footer.append(f"Refs {', '.join(youtrack_refs)}")
        
        if footer:
            message += f"\n\n{chr(10).join(footer)}"
        
        return self.git_commit(message)

    # ==================== PULL REQUESTS ====================
    
    def create_pr(self, title: str, body: str, head: str, base: str = "main") -> dict:
        """Create pull request"""
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        return self._request("POST", f"/repos/{self.repo}/pulls", data)
    
    def get_branch_name(self) -> str:
        """Get current branch name"""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True
        )
        return result.stdout.strip()


class IssueTracker:
    """High-level issue tracking operations"""
    
    def __init__(self, client: GitHubClient = None):
        self.client = client or GitHubClient()
    
    def get_open_bugs(self) -> List[dict]:
        """Get open bug issues"""
        return self.client.get_issues(labels="bug")
    
    def get_open_security(self) -> List[dict]:
        """Get open security issues"""
        return self.client.get_issues(labels="security")
    
    def get_critical_issues(self) -> List[dict]:
        """Get critical/high priority issues"""
        issues = []
        for label in ["priority:critical", "priority:high", "severity:critical", "severity:high"]:
            issues.extend(self.client.get_issues(labels=label))
        return issues
    
    def has_blockers(self) -> bool:
        """Check if there are blocking issues"""
        critical = self.get_critical_issues()
        return len(critical) > 0
    
    def get_developer_tasks(self) -> List[dict]:
        """Get all issues developer should handle"""
        bugs = self.get_open_bugs()
        security = self.get_open_security()
        return bugs + security


# CLI interface
if __name__ == "__main__":
    import sys
    
    client = GitHubClient()
    tracker = IssueTracker(client)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python github_client.py issue list [state] [labels]")
        print("  python github_client.py issue create 'title' 'body' [labels]")
        print("  python github_client.py issue close <number> [comment]")
        print("  python github_client.py bug 'scenario' 'expected' 'actual' 'file'")
        print("  python github_client.py security 'type' 'severity' 'location' 'desc' 'rec'")
        print("  python github_client.py commit <type> <scope> 'subject' [body]")
        print("  python github_client.py push [branch]")
        print("  python github_client.py blockers")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "issue":
        action = sys.argv[2]
        if action == "list":
            state = sys.argv[3] if len(sys.argv) > 3 else "open"
            labels = sys.argv[4] if len(sys.argv) > 4 else None
            issues = client.get_issues(state, labels)
            for i in issues:
                print(f"#{i['number']}: {i['title']} [{i['state']}]")
        elif action == "create":
            labels = sys.argv[5].split(",") if len(sys.argv) > 5 else []
            result = client.create_issue(sys.argv[3], sys.argv[4], labels)
            print(f"Created: #{result.get('number')}")
        elif action == "close":
            comment = sys.argv[4] if len(sys.argv) > 4 else None
            client.close_issue(int(sys.argv[3]), comment)
            print("Closed")
    
    elif cmd == "bug":
        result = client.create_bug_issue(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
        print(f"Bug created: #{result.get('number')}")
    
    elif cmd == "security":
        result = client.create_security_issue(
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
        )
        print(f"Security issue created: #{result.get('number')}")
    
    elif cmd == "commit":
        body = sys.argv[5] if len(sys.argv) > 5 else None
        client.create_conventional_commit(sys.argv[2], sys.argv[3], sys.argv[4], body)
        print("Committed")
    
    elif cmd == "push":
        branch = sys.argv[2] if len(sys.argv) > 2 else None
        client.git_push(branch)
        print("Pushed")
    
    elif cmd == "blockers":
        if tracker.has_blockers():
            print("⚠️ BLOCKERS FOUND:")
            for issue in tracker.get_critical_issues():
                print(f"  #{issue['number']}: {issue['title']}")
        else:
            print("✅ No blockers")
