# TOBU 





## 1) Start runtime (worker + watcher)
```powershell
python backend/search_and_index/desktop_runtime.py
```

## 2) Start API (new terminal)
```powershell
python -m uvicorn backend.search_and_index.api_app:app --host 127.0.0.1 --port 8000 --app-dir C:/Helm/FossHack/TOBU
```

## TODO


1. Implement the desktop UI shell (sidebar explorer, search, jobs, media detail).
2. Wire UI actions to FastAPI endpoints and add error/empty/loading states.
3. Add packaging and one-command startup scripts for local development.
4. Test
