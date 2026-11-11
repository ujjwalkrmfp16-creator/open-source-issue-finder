# Open Source Issue Finder

A Python project that searches GitHub for beginner-friendly open issues and lets you save a personal shortlist.

## Features

- Search open GitHub issues by language, label and keywords.
- Sort by recently updated, created date or comment count.
- Exclude pull requests from issue results.
- Save and remove issues using a local SQLite database.
- FastAPI backend with interactive API documentation.
- Streamlit user interface.
- Basic automated tests.

## Architecture

- `app/github_client.py`: GitHub REST API communication and query construction.
- `app/main.py`: FastAPI routes.
- `app/database.py`: SQLite bookmarks.
- `streamlit_app.py`: Streamlit interface.
- `tests/`: unit tests.

## Requirements

- Python 3.10 or newer.
- Git.
- Optional GitHub personal access token for higher API limits.

## Setup (Windows PowerShell)

```powershell
git clone https://github.com/YOUR-USERNAME/open-source-issue-finder.git
cd open-source-issue-finder
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again.

## Run the application

Open **Terminal 1**:

```powershell
uvicorn app.main:app --reload
```

Open **Terminal 2**:

```powershell
streamlit run streamlit_app.py
```

Open the Streamlit URL printed in Terminal 2 (usually http://localhost:8501).
FastAPI docs are at http://127.0.0.1:8000/docs.

## Optional GitHub token

Create a fine-grained or classic personal access token on GitHub. For public read-only search, do not grant unnecessary repository write permissions. Put it in `.env`:

```text
GITHUB_TOKEN=your_token_here
```

Never commit `.env`, paste the token into source code, or share it in screenshots.

## Run tests

```powershell
pytest -q
```

## Example API request

```text
http://127.0.0.1:8000/issues?language=Python&label=good%20first%20issue&per_page=10
```

## Known limitations / next improvements

This is a learning MVP, not a guarantee that an issue is still unassigned or suitable for a first contribution. Verify every issue on GitHub. Next improvements:

1. Add pagination controls and GitHub rate-limit visibility.
2. Add repository health metrics and contribution-guide detection.
3. Add user accounts and cloud database only if genuinely needed.
4. Add cached searches with expiry and API integration tests.
5. Add GitHub OAuth only when a real user-account feature requires it.
6. Deploy backend and frontend with secrets configured through the host's environment settings.

## Contribution workflow

1. Create an issue describing the proposed change.
2. Fork the repository.
3. Create a focused branch: `git switch -c feat/repository-health`.
4. Make a small change and add/update tests.
5. Run `pytest -q`.
6. Commit with a clear message.
7. Push and open a pull request explaining the problem, solution and test evidence.

## License

MIT. Add the standard MIT license text before publishing if you choose this license.
