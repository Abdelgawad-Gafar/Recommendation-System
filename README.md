# Alluvo Hybrid Recommendation Engine

Minimal setup and run instructions for the recommendation service.

Prerequisites
- Python 3.10+ (3.11 recommended)
- Appropriate SQL Server ODBC driver installed on Windows

Quick start

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd
.\.venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env` and update values (SQL server, user, password, CHROMA_PATH if needed).

4. Run the app:

```bash
uvicorn main:app --reload --port ${PORT:-8000}
```

API notes
- Process a reel: `POST /api/reels/process`
- Update reel metadata: `PUT /api/reels/update-metadata`
- Delete reel (by query param): `DELETE /api/reels/delete?reel_id=<ID>`

Example delete request:

```bash
curl -X DELETE "http://localhost:8000/api/reels/delete?reel_id=12345"
```

Troubleshooting
- If connecting to SQL Server fails, ensure the ODBC driver is installed and `.env` values are correct.
- For GPU support, ensure compatible `torch` and CUDA drivers are installed.

License
This repository contains project work for a graduation project.