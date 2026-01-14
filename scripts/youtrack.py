#!/usr/bin/env python3
"""
YouTrack API Client
Handles tasks, statuses, and Knowledge Base articles
"""

import os
import json
import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class YouTrackClient:
    def __init__(self):
        self.base_url = os.getenv("YOUTRACK_URL", "").rstrip("/")
        self.token = os.getenv("YOUTRACK_TOKEN", "")
        self.project = os.getenv("YOUTRACK_PROJECT", "EXAM")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make API request to YouTrack"""
        url = f"{self.base_url}/api{endpoint}"
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
            print(f"YouTrack API Error: {e}")
            return {"error": str(e)}

    # ==================== ISSUES ====================
    
    def get_issue(self, issue_id: str) -> dict:
        """Get issue details"""
        return self._request("GET", f"/issues/{issue_id}?fields=id,idReadable,summary,description,state(name),customFields(name,value(name))")
    
    def create_issue(self, summary: str, description: str, issue_type: str = "Task") -> dict:
        """Create new issue"""
        data = {
            "project": {"id": self.project},
            "summary": summary,
            "description": description
        }
        return self._request("POST", "/issues?fields=id,idReadable", data)
    
    def update_issue_state(self, issue_id: str, state: str) -> dict:
        """Update issue state (Open, In Progress, Review, Done)"""
        data = {
            "customFields": [
                {
                    "name": "State",
                    "$type": "StateIssueCustomField",
                    "value": {"name": state}
                }
            ]
        }
        return self._request("POST", f"/issues/{issue_id}?fields=id,idReadable,state(name)", data)
    
    def add_comment(self, issue_id: str, text: str) -> dict:
        """Add comment to issue"""
        data = {"text": text}
        return self._request("POST", f"/issues/{issue_id}/comments", data)
    
    def search_issues(self, query: str) -> List[dict]:
        """Search issues with YT query"""
        return self._request("GET", f"/issues?query={query}&fields=id,idReadable,summary,state(name)")
    
    def get_project_issues(self, state: str = None) -> List[dict]:
        """Get all project issues, optionally filtered by state"""
        query = f"project:{self.project}"
        if state:
            query += f" State:{state}"
        return self.search_issues(query)

    # ==================== KNOWLEDGE BASE ====================
    
    def get_articles(self, folder: str = None) -> List[dict]:
        """Get KB articles"""
        endpoint = "/articles?fields=id,idReadable,summary,content,parentArticle(id)"
        if folder:
            endpoint += f"&query=in:{folder}"
        return self._request("GET", endpoint)
    
    def get_article(self, article_id: str) -> dict:
        """Get single KB article"""
        return self._request("GET", f"/articles/{article_id}?fields=id,idReadable,summary,content,updated")
    
    def create_article(self, summary: str, content: str, parent_id: str = None) -> dict:
        """Create KB article"""
        data = {
            "project": {"id": self.project},
            "summary": summary,
            "content": content
        }
        if parent_id:
            data["parentArticle"] = {"id": parent_id}
        return self._request("POST", "/articles?fields=id,idReadable", data)
    
    def update_article(self, article_id: str, content: str = None, summary: str = None) -> dict:
        """Update KB article"""
        data = {}
        if content:
            data["content"] = content
        if summary:
            data["summary"] = summary
        return self._request("POST", f"/articles/{article_id}?fields=id,idReadable", data)
    
    def find_or_create_article(self, path: str, content: str) -> dict:
        """Find article by path or create it"""
        # Search by summary (path)
        articles = self.get_articles()
        for article in articles:
            if article.get("summary") == path:
                return self.update_article(article["id"], content=content)
        # Create new
        return self.create_article(summary=path, content=content)


class KnowledgeBase:
    """High-level Knowledge Base operations"""
    
    def __init__(self, client: YouTrackClient = None):
        self.client = client or YouTrackClient()
        self.cache_file = ".kb_cache.json"
        self._load_cache()
    
    def _load_cache(self):
        """Load KB cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
            else:
                self.cache = {}
        except:
            self.cache = {}
    
    def _save_cache(self):
        """Save KB cache to file"""
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
    
    def read(self, path: str) -> str:
        """Read KB article by path"""
        # Try cache first
        if path in self.cache:
            return self.cache[path].get("content", "")
        
        # Fetch from YouTrack
        articles = self.client.get_articles()
        for article in articles:
            if article.get("summary") == path:
                full = self.client.get_article(article["id"])
                content = full.get("content", "")
                self.cache[path] = {"content": content, "id": article["id"]}
                self._save_cache()
                return content
        return ""
    
    def write(self, path: str, content: str) -> bool:
        """Write/update KB article"""
        result = self.client.find_or_create_article(path, content)
        if "error" not in result:
            self.cache[path] = {"content": content, "id": result.get("id")}
            self._save_cache()
            return True
        return False
    
    def append(self, path: str, content: str) -> bool:
        """Append to existing article"""
        existing = self.read(path)
        new_content = existing + "\n\n" + content if existing else content
        return self.write(path, new_content)
    
    def log_decision(self, decision: str, rationale: str, agent: str):
        """Log architectural decision"""
        timestamp = datetime.now().isoformat()
        entry = f"""
## [{timestamp}] {agent}

**Decision**: {decision}

**Rationale**: {rationale}

---
"""
        self.append("Architecture/decisions.md", entry)
    
    def update_context(self, key: str, value: str, agent: str):
        """Update current context"""
        content = self.read("Context/current-sprint.md") or "# Current Sprint Context\n"
        # Update or add key
        lines = content.split("\n")
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"**{key}**:"):
                lines[i] = f"**{key}**: {value} (updated by {agent})"
                updated = True
                break
        if not updated:
            lines.append(f"**{key}**: {value} (updated by {agent})")
        self.write("Context/current-sprint.md", "\n".join(lines))
    
    def get_context(self) -> dict:
        """Get all current context as dict"""
        content = self.read("Context/current-sprint.md")
        context = {}
        for line in content.split("\n"):
            if line.startswith("**") and "**:" in line:
                key = line.split("**")[1]
                value = line.split("**:")[1].strip() if "**:" in line else ""
                context[key] = value
        return context
    
    def sync(self):
        """Sync cache with YouTrack"""
        articles = self.client.get_articles()
        for article in articles:
            path = article.get("summary", "")
            if path:
                full = self.client.get_article(article["id"])
                self.cache[path] = {
                    "content": full.get("content", ""),
                    "id": article["id"]
                }
        self._save_cache()


# CLI interface
if __name__ == "__main__":
    import sys
    
    client = YouTrackClient()
    kb = KnowledgeBase(client)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python youtrack.py issue get EXAM-42")
        print("  python youtrack.py issue create 'Summary' 'Description'")
        print("  python youtrack.py issue state EXAM-42 'In Progress'")
        print("  python youtrack.py kb read 'Architecture/decisions.md'")
        print("  python youtrack.py kb write 'Path' 'Content'")
        print("  python youtrack.py kb sync")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "issue":
        action = sys.argv[2]
        if action == "get":
            print(json.dumps(client.get_issue(sys.argv[3]), indent=2))
        elif action == "create":
            print(json.dumps(client.create_issue(sys.argv[3], sys.argv[4]), indent=2))
        elif action == "state":
            print(json.dumps(client.update_issue_state(sys.argv[3], sys.argv[4]), indent=2))
        elif action == "comment":
            print(json.dumps(client.add_comment(sys.argv[3], sys.argv[4]), indent=2))
        elif action == "list":
            state = sys.argv[3] if len(sys.argv) > 3 else None
            print(json.dumps(client.get_project_issues(state), indent=2))
    
    elif cmd == "kb":
        action = sys.argv[2]
        if action == "read":
            print(kb.read(sys.argv[3]))
        elif action == "write":
            kb.write(sys.argv[3], sys.argv[4])
            print("OK")
        elif action == "sync":
            kb.sync()
            print("Synced")
        elif action == "context":
            print(json.dumps(kb.get_context(), indent=2))
