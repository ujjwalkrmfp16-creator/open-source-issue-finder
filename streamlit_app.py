import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="Open Source Issue Finder", page_icon="🔎", layout="wide")
st.title("🔎 Open Source Issue Finder")
st.caption("Discover beginner-friendly GitHub issues. Start small, read the contribution guide, and communicate respectfully.")

with st.sidebar:
    st.header("Search filters")
    language = st.selectbox("Programming language", ["Any", "Python", "C++", "Java", "JavaScript", "TypeScript", "Go", "Rust", "Kotlin"])
    label = st.selectbox("Issue label", ["good first issue", "help wanted", "beginner", "documentation"])
    keywords = st.text_input("Keywords (optional)", placeholder="e.g. documentation, bug, API")
    sort = st.selectbox("Sort by", ["updated", "created", "comments"])
    per_page = st.slider("Results per page", 5, 30, 20)
    page = st.number_input("Page", min_value=1, max_value=10, value=1)
    search = st.button("Find issues", type="primary", use_container_width=True)

tab_search, tab_saved = st.tabs(["Discover issues", "Saved issues"])

def api_error_message(response):
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    st.error(f"API error ({response.status_code}): {detail}")

if search or "last_results" not in st.session_state:
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
            with st.container(border=True):
                left, right = st.columns([5, 1])
                with left:
                    st.markdown(f"**[{issue['title']}]({issue['html_url']})**")
                    st.caption(f"{issue['repository']} · #{issue['number']} · by {issue['author']} · {issue['comments']} comments")
                    if issue["labels"]:
                        st.write(" · ".join(f"`{x}`" for x in issue["labels"]))
                    if issue.get("body"):
                        st.write(issue["body"][:350] + ("…" if len(issue["body"]) > 350 else ""))
                with right:
                    if st.button("Save", key=f"save-{issue['id']}"):
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

with tab_saved:
    try:
        response = requests.get(f"{API}/bookmarks", timeout=10)
        response.raise_for_status()
        saved = response.json()
        if not saved:
            st.info("No saved issues yet. Save an issue from the Discover tab.")
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
st.caption("Reminder: labels and issue availability can change. Always open the original GitHub issue and read the repository's CONTRIBUTING.md before starting.")
