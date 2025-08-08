import os, requests, markdown
from django.conf import settings
from django.core.cache import cache

API = "https://api.github.com/repos/{repo}/releases"

def get_recent_releases(limit=3):
    """
    Returns a list of dicts: [{tag, name, published_at, html_body, html_url}]
    """
    cache_key = f"gh_releases:{settings.GITHUB_REPO}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    headers = {"Accept": "application/vnd.github+json"}
    token = getattr(settings, "GITHUB_TOKEN", None)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = API.format(repo=settings.GITHUB_REPO)
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return []

    data = resp.json()[:limit]
    items = []
    for r in data:
        body_md = r.get("body") or ""
        items.append({
            "tag": r.get("tag_name") or r.get("name") or "Unreleased",
            "name": r.get("name") or r.get("tag_name") or "",
            "published_at": r.get("published_at"),
            "html_body": markdown.markdown(body_md, extensions=["extra"]),
            "html_url": r.get("html_url"),
        })

    cache.set(cache_key, items, getattr(settings, "CACHE_RELEASES_SECONDS", 300))
    return items