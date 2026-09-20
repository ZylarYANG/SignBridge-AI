# Backend

当前先保证 FastAPI 最小服务跑通：

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

访问 `http://127.0.0.1:8000/health`。

后续建议拆分：

```text
app/api/
app/services/recognition.py
app/services/assessment.py
app/services/dify_client.py
app/models/
```
