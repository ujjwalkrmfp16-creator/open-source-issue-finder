from app.recommender import estimate_difficulty, enrich_issue, score_issue

def test_beginner_label_reduces_difficulty():
    issue = {"title": "Fix a small typo", "body": "Update README text.", "labels": ["good first issue"], "comments": 0}
    result = estimate_difficulty(issue)
    assert result["difficulty"] == "Beginner"
    assert result["difficulty_score"] <= 30
    assert result["difficulty_reasons"]

def test_advanced_terms_increase_difficulty():
    issue = {"title": "Refactor concurrency architecture", "body": "Resolve a distributed deadlock and memory leak.", "labels": [], "comments": 25}
    result = estimate_difficulty(issue)
    assert result["difficulty"] == "Advanced"
    assert result["difficulty_score"] > 65

def test_difficulty_score_is_bounded():
    issue = {"title": "Migration architecture refactor performance", "body": "x " * 1200, "labels": [], "comments": 40}
    result = estimate_difficulty(issue)
    assert 0 <= result["difficulty_score"] <= 100

def test_enrich_issue_preserves_match_and_adds_difficulty():
    issue = {"title": "Python docs typo", "body": "Fix documentation", "labels": ["good first issue"], "comments": 0}
    result = enrich_issue(issue, ["Python"])
    assert "match_score" in result
    assert result["difficulty"] == "Beginner"
    assert result["difficulty_reasons"]

def test_score_issue_existing_match_thresholds():
    issue = {
        "title": "Improve test coverage",
        "body": "Add automated tests.",
        "labels": [],
        "comments": 0
    }

    result = score_issue(issue, ["Python"])

    assert result["match_score"] == 70
    assert result["match_level"] == "Good match"
