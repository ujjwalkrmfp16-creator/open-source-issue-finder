"""Transparent, rule-based issue matching and difficulty estimation.

These heuristics are explainable indicators, not an AI model or a guarantee
of the actual work required. Always inspect the original issue and repository.
"""
from app.github_client import search_issues, GitHubAPIError
from datetime import datetime, timezone

SUPPORTED_SKILLS = [
    "Python", "C++", "Java", "JavaScript", "TypeScript",
    "Go", "Rust", "Kotlin",
]

BEGINNER_LABELS = {
    "good first issue", "beginner", "beginner-friendly",
    "help wanted", "documentation",
}

def get_recency_score(updated_at, now=None):
    """Give newer issues a higher recency score."""

    if not updated_at:
        return 0

    try:
        updated = datetime.fromisoformat(
            updated_at.replace("Z", "+00:00")
        )

        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)

        updated = updated.astimezone(timezone.utc)

        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        else:
            now = now.astimezone(timezone.utc)

        age_days = max(0, (now - updated).days)

        if age_days <= 7:
            return 100
        elif age_days <= 30:
            return 75
        elif age_days <= 90:
            return 50
        elif age_days <= 180:
            return 25
        else:
            return 0

    except (ValueError, TypeError, AttributeError):
        return 0


def calculate_recommendation_score(issue, now=None):
    """Calculate a final ranking score using multiple issue signals."""

    match_score = issue.get("match_score", 0)
    difficulty_score = issue.get("difficulty_score", 50)

    labels = {
        label.lower()
        for label in issue.get("labels", [])
        if isinstance(label, str)
    }

    strong_beginner_labels = {
        "good first issue",
        "beginner",
        "beginner-friendly",
    }

    supporting_labels = {
        "help wanted",
        "documentation",
    }

    if labels & strong_beginner_labels:
        beginner_signal = 100
    elif labels & supporting_labels:
        beginner_signal = 60
    else:
        beginner_signal = 0

    difficulty_suitability = 100 - difficulty_score
    recency = get_recency_score(issue.get("updated_at"), now)

    recommendation_score = (
        match_score * 0.40
        + beginner_signal * 0.25
        + difficulty_suitability * 0.20
        + recency * 0.15
    )

    return round(recommendation_score, 2)

def score_issue(issue: dict, skills: list[str]) -> dict:
    """Return an issue enriched with a 0-100 skill match score and explanation."""
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    labels = {str(label).lower() for label in issue.get("labels", [])}

    matched_skills = []
    reasons = []
    score = 0

    for skill in skills:
        if skill.lower() in title or skill.lower() in body:
            matched_skills.append(skill)

    if skills:
        score += 60
        reasons.append("Found in a repository matching one of your selected languages")
    if matched_skills:
        score += 15
        reasons.append("Your skill name appears in the issue title or description")
    if labels & BEGINNER_LABELS:
        score += 15
        reasons.append("Has a beginner-friendly or contribution label")
    if title or body:
        score += 10
        reasons.append("Issue includes text that can be reviewed before contributing")

    result = dict(issue)
    result["match_score"] = min(score, 100)
    result["matched_skills"] = matched_skills
    result["matched_languages"] = list(skills)
    result["recommendation_reasons"] = reasons
    if score >= 90:
        result["match_level"] = "Excellent match"
    elif score >= 70:
        result["match_level"] = "Good match"
    elif score >= 50:
        result["match_level"] = "Possible match"
    else:
        result["match_level"] = "Low match"
    return result


def estimate_difficulty(issue: dict) -> dict:
    """Estimate difficulty using visible issue metadata and explain the signals.

    Lower scores indicate more beginner-friendly signals. This deliberately
    avoids claiming to know the real implementation effort from issue text.
    """
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    labels = {str(label).strip().lower() for label in issue.get("labels", [])}
    text = f"{title}\n{body}"
    score = 50
    reasons = []

    beginner_labels = {"good first issue", "beginner", "beginner-friendly"}
    if labels & beginner_labels:
        score -= 25
        reasons.append("Has a beginner-oriented label (-25)")
    if "documentation" in labels or any(word in text for word in (
        "documentation", "docs", "typo", "spelling", "readme"
    )):
        score -= 15
        reasons.append("Documentation or text-maintenance signal (-15)")
    if "help wanted" in labels:
        score -= 10
        reasons.append("Has a help-wanted label (-10)")

    advanced_terms = {
        "architecture", "refactor", "migration", "performance",
        "concurrency", "security", "memory leak", "deadlock",
        "distributed", "breaking change",
    }
    found_advanced = sorted(term for term in advanced_terms if term in text)
    if found_advanced:
        score += min(10 * len(found_advanced), 30)
        reasons.append("Complexity terms found: " + ", ".join(found_advanced))

    implementation_terms = ("implement", " redesign", "rewrite", "support ")
    found_implementation = [term.strip() for term in implementation_terms if term in text]
    if found_implementation:
        score += 10
        reasons.append("Implementation or redesign wording (+10)")

    if len(body) > 1800:
        score += 10
        reasons.append("Long issue description may require more investigation (+10)")
    if issue.get("comments", 0) >= 20:
        score += 10
        reasons.append("Many discussion comments may indicate complexity (+10)")

    score = max(0, min(100, score))
    if score <= 30:
        level = "Beginner"
    elif score <= 65:
        level = "Intermediate"
    else:
        level = "Advanced"

    if not reasons:
        reasons.append("No strong beginner or complexity signals detected; inspect the issue manually")
    return {
        "difficulty_score": score,
        "difficulty": level,
        "difficulty_reasons": reasons,
        "difficulty_note": "Heuristic estimate based on labels, wording, description length and discussion count.",
    }


def enrich_issue(issue: dict, skills: list[str]) -> dict:
    """Add both skill-match and difficulty information."""
    return {**score_issue(issue, skills), **estimate_difficulty(issue)}


def recommend_issues(skills: list[str], label="good first issue",
                     keywords=None, per_page=10, page=1):
    """Search each selected language, deduplicate, score and rank issues."""
    clean_skills = list(dict.fromkeys(
        skill.strip() for skill in skills if skill and skill.strip()
    ))
    if not clean_skills:
        raise ValueError("Select at least one programming skill.")

    unknown = [skill for skill in clean_skills if skill not in SUPPORTED_SKILLS]
    if unknown:
        raise ValueError("Unsupported skill(s): " + ", ".join(unknown))

    combined = {}
    queries = []
    for skill in clean_skills:
        result = search_issues(
            language=skill, label=label, keywords=keywords,
            sort="updated", order="desc", per_page=per_page, page=page,
        )
        queries.append(result["query"])
        for issue in result["items"]:
            if issue["id"] not in combined:
                combined[issue["id"]] = {"issue": issue, "matched_languages": []}
            combined[issue["id"]]["matched_languages"].append(skill)

    scored = [
        enrich_issue(entry["issue"], entry["matched_languages"])
        for entry in combined.values()
    ]

    for issue in scored:
        issue["recommendation_score"] = calculate_recommendation_score(issue)

    ranked = sorted(
        scored,
        key=lambda item: (
            item["recommendation_score"],
            item["match_score"],
            item.get("updated_at", ""),
        ),
        reverse=True,
    )
    return {
        "skills": clean_skills,
        "total_count": len(ranked),
        "items": ranked[:per_page],
        "queries": queries,
        "scoring_note": (
            "Skill matching and difficulty are transparent rule-based heuristics, "
            "not AI predictions. Review the original issue before contributing."
        ),
    }
