from app.github_client import build_search_query

def test_query_has_open_issue_filters():
    query = build_search_query(language="Python", label="good first issue")
    assert "is:issue" in query
    assert "is:open" in query
    assert "archived:false" in query
    assert 'label:"good first issue"' in query
    assert "language:Python" in query

def test_query_without_optional_filters():
    query = build_search_query(language=None, label=None, keywords="documentation")
    assert "is:issue" in query
    assert "documentation" in query
    assert "language:" not in query
