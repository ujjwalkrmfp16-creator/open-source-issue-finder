from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from app.database import init_db, add_bookmark, get_bookmarks, delete_bookmark
from app.github_client import search_issues, GitHubAPIError
from app.schemas import BookmarkCreate

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Open Source Issue Finder API",
    description="Find beginner-friendly GitHub issues and save issues to a local reading list.",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/issues")
def issues(
    language: str | None = None,
    label: str = "good first issue",
    keywords: str | None = None,
    sort: str = Query("updated", pattern="^(created|updated|comments)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    per_page: int = Query(20, ge=1, le=30),
    page: int = Query(1, ge=1, le=10),
):
    try:
        return search_issues(language, label, keywords, sort, order, per_page, page)
    except GitHubAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

@app.get("/bookmarks")
def bookmarks():
    return get_bookmarks()

@app.post("/bookmarks", status_code=201)
def create_bookmark(bookmark: BookmarkCreate):
    return add_bookmark(bookmark)

@app.delete("/bookmarks/{github_id}")
def remove_bookmark(github_id: int):
    if not delete_bookmark(github_id):
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"deleted": True, "github_id": github_id}
