import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
LANGUAGES = ["Python", "C++", "Java", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin"]

st.set_page_config(page_title="Open Source Issue Finder", page_icon="🔎", layout="wide")
st.title("🔎 Open Source Issue Finder")
st.caption("Discover beginner-friendly GitHub issues. Start small, read the contribution guide, and communicate respectfully.")

with st.sidebar:
    st.header("Search filters")
    language = st.selectbox("Programming language", ["Any"] + LANGUAGES)
    label = st.selectbox("Issue label", ["good first issue", "help wanted", "beginner", "documentation"])
    keywords = st.text_input("Keywords (optional)", placeholder="e.g. documentation, bug, API")
    sort = st.selectbox("Sort by", ["updated", "created", "comments"])
    per_page = st.slider("Results per page", 5, 30, 20)
    page = st.number_input("Page", min_value=1, max_value=10, value=1)
    search = st.button("Find issues", type="primary", use_container_width=True)

tab_search, tab_recommend, tab_saved = st.tabs(
    ["Discover issues", "Skill recommendations", "Saved issues"]
)

if search or "last_results" not in st.session_state:
    with st.spinner("Searching GitHub..."):
        try:
            params = {
                "language": None if language == "Any" else language,
                "label": label, "keywords": keywords or None,
                "sort": sort, "per_page": per_page, "page": page,
            }
            response = requests.get(f"{API}/issues", params=params, timeout=25)
            response.raise_for_status()
            st.session_state["last_results"] = response.json()
        except requests.RequestException as exc:
            st.session_state.pop("last_results", None)
            st.error(f"Could not reach the backend. Start FastAPI first. Details: {exc}")

def render_issue(issue, key_prefix="issue"):
    with st.container(border=True):
        left, right = st.columns([5, 1])
        with left:
            st.markdown(f"**[{issue['title']}]({issue['html_url']})**")
            st.caption(f"{issue['repository']} · #{issue['number']} · by {issue['author']} · {issue['comments']} comments")
            if issue.get("labels"):
                st.write(" · ".join(f"`{x}`" for x in issue["labels"]))
            if issue.get("body"):
                st.write(issue["body"][:350] + ("…" if len(issue["body"]) > 350 else ""))
            if "match_score" in issue:
                st.progress(issue["match_score"] / 100)
                st.write(f"**{issue['match_level']} — {issue['match_score']}/100**")
                st.caption("Why recommended: " + "; ".join(issue["recommendation_reasons"]))
        with right:
            if st.button("Save", key=f"{key_prefix}-{issue['id']}"):
                try:
                    r = requests.post(f"{API}/bookmarks", json={
                        "github_id": issue["id"], "title": issue["title"],
                        "html_url": issue["html_url"], "repository": issue["repository"],
                        "number": issue["number"],
                    }, timeout=10)
                    r.raise_for_status()
                    st.success("Saved")
                except requests.RequestException as exc:
                    st.error(f"Could not save: {exc}")

with tab_search:
    data = st.session_state.get("last_results")
    if data:
        st.write(f"Showing **{len(data['items'])}** results. GitHub reports approximately **{data['total_count']}** matches.")
        if data.get("incomplete_results"):
            st.warning("GitHub marked these search results as incomplete.")
        st.caption(f"GitHub query: `{data['query']}`")
        if not data["items"]:
            st.info("No issues found. Try removing keywords or changing the label.")
        for issue in data["items"]:
            render_issue(issue, "discover")

with tab_recommend:
    st.subheader("Find issues that match your skills")
    st.write("Choose the programming languages you know. The app searches matching repositories and ranks issues using a transparent rule-based score.")
    selected_skills = st.multiselect(
        "Your programming skills",
        LANGUAGES,
        default=["Python"],
        help="Select one or more languages you can use to contribute.",
    )
    rec_label = st.selectbox(
        "Preferred issue label",
        ["good first issue", "help wanted", "beginner", "documentation"],
        key="recommend_label",
    )
    rec_keywords = st.text_input(
        "Optional topic keywords", placeholder="e.g. API, testing, documentation",
        key="recommend_keywords",
    )
    if st.button("Get my recommendations", type="primary"):
        if not selected_skills:
            st.warning("Select at least one programming skill.")
        else:
            with st.spinner("Finding issues that match your skills..."):
                try:
                    response = requests.get(
                        f"{API}/recommendations",
                        params=[
                            *[("skills", skill) for skill in selected_skills],
                            ("label", rec_label),
                            ("keywords", rec_keywords or ""),
                            ("per_page", 20),
                            ("page", 1),
                        ],
                        timeout=60,
                    )
                    response.raise_for_status()
                    st.session_state["recommendations"] = response.json()
                except requests.RequestException as exc:
                    st.error(f"Recommendation request failed: {exc}")

    recommendations = st.session_state.get("recommendations")
    if recommendations:
        st.success(f"Found {recommendations['total_count']} unique recommendations for: {', '.join(recommendations['skills'])}")
        st.caption(recommendations["scoring_note"])
        if not recommendations["items"]:
            st.info("No matching issues found. Try another label or remove the topic keywords.")
        for issue in recommendations["items"]:
            render_issue(issue, "recommend")

with tab_saved:
    try:
        response = requests.get(f"{API}/bookmarks", timeout=10)
        response.raise_for_status()
        saved = response.json()
        if not saved:
            st.info("No saved issues yet. Save an issue from the Discover or Recommendations tab.")
        for item in saved:
            with st.container(border=True):
                st.markdown(f"**[{item['title']}]({item['html_url']})**")
                st.caption(f"{item['repository']} · #{item['issue_number']} · saved {item['saved_at']}")
                if st.button("Remove", key=f"remove-{item['github_id']}"):
                    try:
                        r = requests.delete(f"{API}/bookmarks/{item['github_id']}", timeout=10)
                        r.raise_for_status()
                        st.rerun()
                    except requests.RequestException as exc:
                        st.error(f"Could not remove: {exc}")
    except requests.RequestException as exc:
        st.warning(f"Could not load saved issues: {exc}")

st.divider()
st.caption("Reminder: recommendations are heuristic, not guarantees. Always open the original GitHub issue and read the repository's CONTRIBUTING.md before starting.")
