# TOBU Run

Run from project root (`C:/Helm/FossHack/TOBU`).



## 1) Start runtime (worker + watcher)
```powershell
python backend/search_and_index/desktop_runtime.py
```

## 2) Start API (new terminal)
```powershell
python -m uvicorn backend.search_and_index.api_app:app --host 127.0.0.1 --port 8000 --app-dir C:/Helm/FossHack/TOBU
```
