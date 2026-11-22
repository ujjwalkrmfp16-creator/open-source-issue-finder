
import pytest
import requests
from unittest.mock import Mock, patch

from app.github_client import (
    build_search_query,
    search_issues,
    GitHubAPIError,
)


def test_query_has_open_issue_filters():
    query = build_search_query(language="Python", label="good first issue")

    assert "is:issue" in query
    assert "is:open" in query
    assert "archived:false" in query
    assert 'label:"good first issue"' in query
    assert "language:Python" in query


def test_query_without_optional_filters():
    query = build_search_query(
        language=None,
        label=None,
        keywords="documentation",
    )

    assert "is:issue" in query
    assert "documentation" in query
    assert "language:" not in query


def test_github_authentication_error():
    response = Mock()
    response.status_code = 401
    response.ok = False
    response.headers = {}

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="authentication failed"):
            search_issues()


def test_github_rate_limit_error():
    response = Mock()
    response.status_code = 403
    response.ok = False
    response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": "1790000000",
    }

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="rate limit exceeded"):
            search_issues()


def test_github_too_many_requests_error():
    response = Mock()
    response.status_code = 429
    response.ok = False
    response.headers = {"Retry-After": "30"}

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="30 seconds"):
            search_issues()


def test_github_server_error():
    response = Mock()
    response.status_code = 500
    response.ok = False
    response.headers = {}

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="server problem"):
            search_issues()


def test_github_invalid_json_response():
    response = Mock()
    response.ok = True
    response.json.side_effect = requests.exceptions.JSONDecodeError(
        "Invalid JSON", "not json", 0
    )

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="invalid JSON"):
            search_issues()


def test_github_unexpected_response_format():
    response = Mock()
    response.ok = True
    response.json.return_value = {"message": "Unexpected response"}

    with patch("app.github_client.requests.get", return_value=response):
        with pytest.raises(GitHubAPIError, match="unexpected response format"):
            search_issues()

def test_github_connection_timeout():
    with patch(
        "app.github_client.requests.get",
        side_effect=requests.exceptions.Timeout("Request timed out"),
    ):
        with pytest.raises(GitHubAPIError, match="Could not connect to GitHub"):
            search_issues()


def test_github_connection_error():
    with patch(
        "app.github_client.requests.get",
        side_effect=requests.exceptions.ConnectionError("Network unavailable"),
    ):
        with pytest.raises(GitHubAPIError, match="Could not connect to GitHub"):
            search_issues()

def test_github_issue_with_missing_optional_fields():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "id": 123,
                "title": "Test issue"
            }
        ]
    }

    with patch(
        "app.github_client.requests.get",
        return_value=mock_response,
    ):
        result = search_issues()

    assert len(result["items"]) == 1
    assert result["items"][0]["title"] == "Test issue"
    assert result["items"][0]["body"] == ""
    assert result["items"][0]["author"] == "unknown"
    assert result["items"][0]["labels"] == []

def test_github_pagination_parameters():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "total_count": 0,
        "incomplete_results": False,
        "items": []
    }

    with patch(
        "app.github_client.requests.get",
        return_value=mock_response,
    ) as mock_get:
        result = search_issues(per_page=10, page=2)

    params = mock_get.call_args.kwargs["params"]

    assert params["per_page"] == 10
    assert params["page"] == 2
    assert result["page"] == 2
    assert result["per_page"] == 10

def test_invalid_page_number():
    with pytest.raises(ValueError, match="Page must be at least 1"):
        search_issues(page=0)


def test_invalid_per_page_too_small():
    with pytest.raises(ValueError, match="per_page must be between 1 and 100"):
        search_issues(per_page=0)


def test_invalid_per_page_too_large():
    with pytest.raises(ValueError, match="per_page must be between 1 and 100"):
        search_issues(per_page=101)

def test_pull_requests_are_excluded():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "total_count": 2,
        "incomplete_results": False,
        "items": [
            {
                "id": 101,
                "title": "Add documentation",
                "repository_url": "https://api.github.com/repos/example/project",
            },
            {
                "id": 102,
                "title": "Fix bug",
                "pull_request": {
                    "url": "https://api.github.com/repos/example/project/pulls/2"
                },
            },
        ],
    }

    with patch(
        "app.github_client.requests.get",
        return_value=mock_response,
    ):
        result = search_issues()

    assert len(result["items"]) == 1
    assert result["items"][0]["id"] == 101
    assert result["items"][0]["title"] == "Add documentation"

def test_repository_name_extraction():
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "total_count": 1,
        "incomplete_results": False,
        "items": [
            {
                "id": 201,
                "title": "Improve tests",
                "repository_url": (
                    "https://api.github.com/repos/openai/example-project"
                ),
            }
        ],
    }

    with patch(
        "app.github_client.requests.get",
        return_value=mock_response,
    ):
        result = search_issues()

    assert result["items"][0]["repository"] == "openai/example-project"