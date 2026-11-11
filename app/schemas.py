from pydantic import BaseModel, Field
from typing import Optional

class Issue(BaseModel):
    id: int
    title: str
    html_url: str
    repository: str
    repository_url: str
    number: int
    state: str
    created_at: str
    updated_at: str
    comments: int
    labels: list[str] = Field(default_factory=list)
    body: Optional[str] = None
    author: str

class BookmarkCreate(BaseModel):
    github_id: int
    title: str
    html_url: str
    repository: str
    number: int
