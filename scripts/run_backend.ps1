$env:PYTHONPATH = "$PSScriptRoot\..\backend"
uvicorn app.main:app --app-dir "$PSScriptRoot\..\backend" --reload --host 127.0.0.1 --port 8000
