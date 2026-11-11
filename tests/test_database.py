from app import database
from app.schemas import BookmarkCreate

def test_bookmark_crud(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", str(tmp_path / "test.db"))
    database.init_db()
    item = BookmarkCreate(
        github_id=123, title="Fix typo", html_url="https://github.com/a/b/issues/1",
        repository="a/b", number=1
    )
    database.add_bookmark(item)
    saved = database.get_bookmarks()
    assert len(saved) == 1
    assert saved[0]["title"] == "Fix typo"
    assert database.delete_bookmark(123) is True
    assert database.get_bookmarks() == []
