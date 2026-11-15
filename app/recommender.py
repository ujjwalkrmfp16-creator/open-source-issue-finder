"""Transparent, rule-based skill matching for GitHub issues.

This is intentionally not presented as an AI model: scores are deterministic
heuristics that users can inspect and improve.
"""
from app.github_client import search_issues, GitHubAPIError

SUPPORTED_SKILLS = [
    "Python", "C++", "Java", "JavaScript", "TypeScript",
    "Go", "Rust", "Kotlin",
]

BEGINNER_LABELS = {
    "good first issue", "beginner", "beginner-friendly",
    "help wanted", "documentation",
}

def score_issue(issue: dict, skills: list[str]) -> dict:
    """Return an issue enriched with a 0-100 match score and explanation."""
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    labels = {str(label).lower() for label in issue.get("labels", [])}

    matched_skills = []
    reasons = []
    score = 0

    # The search was made for this language, so each candidate has a
    # language-level match. Award 60 points for the strongest signal.
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

    issue = dict(issue)
    issue["match_score"] = min(score, 100)
    issue["matched_skills"] = matched_skills or list(skills)
    issue["recommendation_reasons"] = reasons
    if score >= 90:
        issue["match_level"] = "Excellent match"
    elif score >= 70:
        issue["match_level"] = "Good match"
    elif score >= 50:
        issue["match_level"] = "Possible match"
    else:
        issue["match_level"] = "Low match"
    return issue


def recommend_issues(skills: list[str], label="good first issue",
                     keywords=None, per_page=10, page=1):
    """Search each selected language, deduplicate, score and rank issues."""
    clean_skills = list(dict.fromkeys(
        skill.strip() for skill in skills if skill and skill.strip()
    ))
    if not clean_skills:
        raise ValueError("Select at least one programming skill.")

    unknown = [skill for skill in clean_skills
               if skill not in SUPPORTED_SKILLS]
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
        score_issue(entry["issue"], entry["matched_languages"])
        for entry in combined.values()
    ]
    ranked = sorted(
        scored,
        key=lambda item: (
            item["match_score"],
            item.get("updated_at", ""),
            -item.get("comments", 0),
        ),
        reverse=True,
    )
    return {
        "skills": clean_skills,
        "total_count": len(ranked),
        "items": ranked[:per_page],
        "queries": queries,
        "scoring_note": (
            "Rule-based heuristic, not an AI prediction. Scores use selected "
            "language, skill mentions, beginner labels and issue text."
        ),
    }
