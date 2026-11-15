from app.recommender import score_issue

def sample_issue():
    return {
        "id": 123,
        "title": "Add Python unit tests",
        "body": "Improve test coverage for the API.",
        "labels": ["good first issue"],
        "updated_at": "2026-11-01T00:00:00Z",
        "comments": 2,
    }

def test_score_contains_explanation_and_is_bounded():
    result = score_issue(sample_issue(), ["Python"])
    assert 0 <= result["match_score"] <= 100
    assert result["match_level"] == "Excellent match"
    assert result["matched_skills"] == ["Python"]
    assert result["recommendation_reasons"]

def test_score_without_skill_mention_still_uses_search_language_signal():
    issue = sample_issue()
    issue["title"] = "Improve test coverage"
    issue["body"] = "Add automated tests."
    result = score_issue(issue, ["Python"])
    assert result["match_score"] == 85
    assert result["match_level"] == "Good match"
