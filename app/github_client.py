import requests
from app.config import GITHUB_API_BASE, GITHUB_TOKEN

class GitHubAPIError(Exception):
    pass

def build_search_query(language=None, label="good first issue", keywords=None):
    # Search syntax is documented by GitHub. Quote multi-word labels.
    parts = ["is:issue", "is:open", "archived:false"]
    if label:
        safe_label = label.replace('"', r'\\"')
        parts.append(f'label:"{safe_label}"')
    if language:
        safe_language = language.replace('"', "").strip()
        parts.append(f'language:{safe_language}')
    if keywords:
        parts.append(keywords.strip())
    return " ".join(parts)

def _headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers

def _get_error_message(response):
    """Create a useful error message from a GitHub API response."""

    status = response.status_code
    headers = response.headers

    if status == 401:
        return (
            "GitHub authentication failed. Check your personal "
            "access token in the .env file."
        )

    if status in (403, 429):
        remaining = headers.get("X-RateLimit-Remaining")
        reset = headers.get("X-RateLimit-Reset")
        retry_after = headers.get("Retry-After")

        if remaining == "0":
            return (
                "GitHub API rate limit exceeded. "
                f"Try again after Unix timestamp {reset}."
                if reset
                else "GitHub API rate limit exceeded. Please retry later."
            )

        if retry_after:
            return (
                "GitHub temporarily limited your requests. "
                f"Retry after {retry_after} seconds."
            )

        return (
            "GitHub denied the request. Check your token permissions "
            "or retry later."
        )

    if status == 422:
        return (
            "GitHub rejected the search query. "
            "Try simpler filters."
        )

    if status >= 500:
        return (
            f"GitHub is experiencing a server problem (HTTP {status}). "
            "Please retry later."
        )

    return f"GitHub API returned HTTP {status}."

def search_issues(language=None, label="good first issue", keywords=None,
                  sort="updated", order="desc", per_page=20, page=1):
    if page < 1:
        raise ValueError("Page must be at least 1.")

    if not 1 <= per_page <= 100:
        raise ValueError("per_page must be between 1 and 100.")
    query = build_search_query(language, label, keywords)
    url = f"{GITHUB_API_BASE}/search/issues"
    try:
        response = requests.get(
            url,
            headers=_headers(),
            params={
                "q": query, "sort": sort, "order": order,
                "per_page": per_page, "page": page,
            },
            timeout=20,
        )
    except requests.RequestException as exc:
        raise GitHubAPIError(f"Could not connect to GitHub: {exc}") from exc

    if not response.ok:
        raise GitHubAPIError(_get_error_message(response))

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        raise GitHubAPIError(
            "GitHub returned an invalid JSON response. Please retry later."
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise GitHubAPIError(
            "GitHub returned an unexpected response format."
        )
    results = []
    for item in payload.get("items", []):
        # Search issues can include pull requests; exclude them explicitly.
        if "pull_request" in item:
            continue
        repo_url = item.get("repository_url", "")
        repo_name = "/".join(repo_url.rstrip("/").split("/")[-2:])
        results.append({
            "id": item["id"],
            "title": item.get("title", ""),
            "html_url": item.get("html_url", ""),
            "repository": repo_name,
            "repository_url": repo_url,
            "number": item.get("number", 0),
            "state": item.get("state", ""),
            "created_at": item.get("created_at", ""),
            "updated_at": item.get("updated_at", ""),
            "comments": item.get("comments", 0),
            "labels": [x.get("name", "") for x in item.get("labels", [])],
            "body": item.get("body") or "",
            "author": (item.get("user") or {}).get("login", "unknown"),
        })
    return {
        "total_count": payload.get("total_count", 0),
        "incomplete_results": payload.get("incomplete_results", False),
        "page": page,
        "per_page": per_page,
        "query": query,
        "items": results,
    }
