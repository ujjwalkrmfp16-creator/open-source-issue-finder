from app.recommender import score_issue
from datetime import datetime, timezone
from app.recommender import (
    score_issue,
    get_recency_score,
    calculate_recommendation_score,
)

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
def test_matched_skills_contains_only_mentioned_skills():
    issue = {
        "title": "Fix Python API validation",
        "body": "Improve input validation.",
        "labels": [],
    }

    result = score_issue(issue, ["Python", "Java"])

    assert result["matched_skills"] == ["Python"]
    assert result["matched_languages"] == ["Python", "Java"]


def test_matched_skills_is_empty_when_not_mentioned():
    issue = {
        "title": "Fix CSS layout",
        "body": "Improve responsive design.",
        "labels": [],
    }

    result = score_issue(issue, ["Python"])

    assert result["matched_skills"] == []
    assert result["matched_languages"] == ["Python"]


def test_multiple_skills_are_matched():
    issue = {
        "title": "Improve Python and Java integration",
        "body": "Update the integration tests.",
        "labels": [],
    }

    result = score_issue(issue, ["Python", "Java", "Go"])

    assert result["matched_skills"] == ["Python", "Java"]


def test_skill_matching_is_case_insensitive():
    issue = {
        "title": "Improve PYTHON API",
        "body": "Update documentation.",
        "labels": [],
    }

    result = score_issue(issue, ["Python"])

    assert result["matched_skills"] == ["Python"]

def test_recent_issue_gets_higher_recency_score():
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)

    recent = get_recency_score(
        "2026-11-18T00:00:00Z", now
    )

    old = get_recency_score(
        "2026-04-01T00:00:00Z", now
    )

    assert recent > old
    assert recent == 100
    assert old == 0


def test_invalid_date_gets_zero_recency_score():
    assert get_recency_score("invalid-date") == 0


def test_beginner_issue_gets_higher_recommendation_score():
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)

    beginner_issue = {
        "match_score": 85,
        "difficulty_score": 25,
        "labels": ["good first issue"],
        "updated_at": "2026-11-18T00:00:00Z",
    }

    advanced_issue = {
        "match_score": 85,
        "difficulty_score": 80,
        "labels": [],
        "updated_at": "2026-11-18T00:00:00Z",
    }

    beginner_score = calculate_recommendation_score(
        beginner_issue, now
    )

    advanced_score = calculate_recommendation_score(
        advanced_issue, now
    )

    assert beginner_score > advanced_score


def test_recommendation_score_is_bounded():
    issue = {
        "match_score": 100,
        "difficulty_score": 0,
        "labels": ["good first issue"],
        "updated_at": "2026-11-18T00:00:00Z",
    }

    score = calculate_recommendation_score(
        issue,
        datetime(2026, 11, 20, tzinfo=timezone.utc),
    )

    assert 0 <= score <= 100