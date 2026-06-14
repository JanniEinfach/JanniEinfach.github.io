#!/usr/bin/env python3
"""
Syncs projects.json with public GitHub repos from JanniEinfach.
- New repos get added with category "other" (auto-discovered)
- Existing entries are NOT overwritten (manual curation is preserved)
- Only star counts are updated for existing entries
"""
import json, os, urllib.request, urllib.error

GITHUB_USER = "JanniEinfach"
PROJECTS_FILE = os.path.join(os.path.dirname(__file__), "..", "projects.json")

# Repos to always ignore (forks, profile README, etc.)
IGNORE = {"JanniEinfach", "JanniEinfach.github.io"}

def fetch_repos(token=None):
    url = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&sort=updated&type=public"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "sync-projects"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.load(r)

def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repos = fetch_repos(token)

    with open(PROJECTS_FILE) as f:
        projects = json.load(f)

    existing = {p["name"]: i for i, p in enumerate(projects)}
    changed = False

    for repo in repos:
        name = repo["name"]
        if repo.get("fork") or name in IGNORE:
            continue

        if name in existing:
            # Only update star count, keep everything else
            idx = existing[name]
            stars = repo.get("stargazers_count", 0)
            if projects[idx].get("stars") != stars:
                projects[idx]["stars"] = stars
                changed = True
        else:
            # New repo — add with safe defaults, category "other"
            topics = repo.get("topics") or []
            projects.append({
                "name": name,
                "display": name,
                "category": "other",
                "featured": False,
                "description": repo.get("description") or "",
                "tags": topics,
                "url": repo["html_url"],
                "stars": repo.get("stargazers_count", 0),
                "auto_added": True
            })
            existing[name] = len(projects) - 1
            changed = True
            print(f"[sync] Added new repo: {name}")

    if changed:
        with open(PROJECTS_FILE, "w") as f:
            json.dump(projects, f, indent=2, ensure_ascii=False)
        print("[sync] projects.json updated.")
    else:
        print("[sync] No changes.")

if __name__ == "__main__":
    main()
