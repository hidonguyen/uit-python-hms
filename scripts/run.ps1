
# Run FastAPI in dev (Windows PowerShell)
if (-not (Test-Path ".\.venv")) {
    py -3 -m venv .venv
}
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
