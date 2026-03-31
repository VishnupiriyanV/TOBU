<div align="center">

#  TOBU

### Your Personal Multimodal Knowledge Vault

*Drop in videos, PDFs, and notes. Ask anything. Get exact answers with timestamps.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Electron](https://img.shields.io/badge/Electron-30-47848F?style=flat-square&logo=electron)](https://electronjs.org)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?style=flat-square&logo=react)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What Is TOBU?

TOBU is a **fully offline desktop application** that turns your personal archive of videos, PDFs, and plain-text notes into a searchable, queryable knowledge base,no cloud, no subscriptions, no data leaving your machine.

Drop a lecture recording into the vault. Ask *"what did they say about gradient descent?"* and TOBU will surface the exact transcript segment with a timestamp, along with the visual frame from that moment.

**Why it matters:** Most personal knowledge tools index filenames and metadata. TOBU indexes *what's inside* : speech, visual content, and text and retrieves it semantically. It bridges the gap between "I know I watched something about this" and actually finding it.

---

## Feature Overview

| Category | Capability |
|---|---|
|  **Video** | Speech-to-text transcription (Whisper), CLIP frame embeddings, thumbnail extraction |
|  **Documents** | PDF page-level extraction (PyMuPDF), Markdown / `.txt` paragraph chunking |
|  **Search** | Hybrid semantic + keyword search with Reciprocal Rank Fusion (RRF) |
|  **Summarization** | Auto-generated summaries via DistilBART for every indexed file |
|  **Watch Folder** | Drop files in; auto-detection, debounced stability checks, auto-enqueue |
|  **Desktop App** | Electron shell + PyInstaller backend — single installer, zero runtime deps |
| **Job Queue** | SQLite-backed job queue with retry logic, progress tracking, and cancellation |
|  **Privacy First** | 100% local inference. All models run on-device. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Electron Shell (desktop/)                  │
│  main.js → spawns Python backend → loads React UI           │
└─────────────────┬───────────────────────────────────────────┘
                  │ http://127.0.0.1:8000
┌─────────────────▼───────────────────────────────────────────┐
│              FastAPI Backend (backend/search_and_index/)      │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ aural_engine│  │visual_engine │  │  document_engine  │   │
│  │  (Whisper)  │  │   (CLIP)     │  │ (PyMuPDF/frontmatter)│ │
│  └──────┬──────┘  └──────┬───────┘  └─────────┬─────────┘   │
│         │                │                     │             │
│  ┌──────▼────────────────▼─────────────────────▼───────────┐ │
│  │            semantic_engine (MiniLM + LanceDB)           │ │
│  │          Hybrid RRF Search (semantic + keyword)         │ │
│  └────────────────────────┬────────────────────────────────┘ │
│                           │                                   │
│  ┌────────────────────────▼────────────────────────────────┐ │
│  │         sql_database.py  (SQLite — jobs + media)        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────────┐   ┌───────────────────────────────┐│
│  │  watchdog FileWatcher│   │  Background Worker Thread     ││
│  │  (auto-enqueue files)│   │  (job queue consumer)         ││
│  └──────────────────────┘   └───────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│             React Frontend (client/ — Vite + JSX)           │
│   Search · Jobs · Ingest · System panels                    │
└─────────────────────────────────────────────────────────────┘
```

### AI Models Used (all run locally)

| Model | Purpose | Source |
|---|---|---|
| `distil-large-v3` | Speech-to-text transcription | [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) |
| `clip-ViT-B-32` | Visual frame understanding & search | [CLIP via sentence-transformers](https://huggingface.co/sentence-transformers/clip-ViT-B-32) |
| `all-MiniLM-L6-v2` | Semantic text embeddings | [sentence-transformers](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) |
| `distilbart-cnn-6-6` | Automatic content summarization | [sshleifer/distilbart-cnn-6-6](https://huggingface.co/sshleifer/distilbart-cnn-6-6) |

---

## Requirements

### System

- **OS:** Windows 10/11 (64-bit) · macOS 12+ · Linux (Ubuntu 20.04+)
- **Python:** 3.10 or later
- **Node.js:** 18 or later
- **FFmpeg:** Must be on your system `PATH` ([Download here](https://ffmpeg.org/download.html))
- **RAM:** 8 GB minimum (16 GB recommended)
- **GPU:** Optional — CUDA 12 supported for faster transcription

### Supported File Types

| Type | Extensions |
|---|---|
| Video | `.mp4` `.mkv` `.avi` `.mov` `.webm` |
| Documents | `.pdf` |
| Notes | `.md` `.txt` |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/VishnupiriyanV/TOBU.git
cd TOBU
```

### 2. Set Up the Python Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r backend/search_and_index/requirements.txt
```

> **GPU Acceleration (Optional):** If you have an NVIDIA GPU with CUDA 12, uncomment the CUDA lines in `requirements.txt` before installing.

### 3. Install Node Dependencies

```bash
# Root (Electron shell)
npm install

# React frontend
cd client && npm install && cd ..
```

### 4. Download AI Models

On first launch, TOBU's onboarding wizard handles model downloads automatically.  
To pre-download manually:

```bash
python backend/search_and_index/model_downloader.py
```

This downloads ~1.5 GB of models into the `models/` directory.

---

## Running in Development

```bash
# Terminal 1 — Start the FastAPI backend
python -m uvicorn backend.search_and_index.api_app:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2 — Start the full Electron + React app
npm start
```

The Electron window will open automatically once the React dev server is ready on `http://localhost:5173`.

---

## Building for Distribution

A single PowerShell script handles the full build pipeline:

```powershell
.\build_tobu.ps1
```

This will:
1. Build the React frontend (`client/dist/`)
2. Sync the UI into the Electron shell (`desktop/ui/`)
3. Bundle the Python backend with PyInstaller
4. Package everything into a desktop installer via `electron-builder`

The output installer will be in `desktop/release/`.

---

## Testing

### Smoke Test the API

```bash
# With the backend running on port 8000
python test_api_smoke.py
```

### Check Backend Health

```bash
curl http://127.0.0.1:8000/api/v1/health
```

### Manually Index a File

```bash
# Drop a file into the watch folder; it will be auto-detected and queued
cp my_video.mp4 watch/

# Or POST directly to the ingest API
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/absolute/path/to/my_video.mp4"}'
```

### Query the Search API

```bash
curl "http://127.0.0.1:8000/api/v1/search?q=gradient+descent&limit=5"
```

---

## How TOBU Processes a File

Below is the full indexing pipeline for a video file:

```
File dropped into watch/ folder
        │
        ▼
FileWatcher (watchdog) detects change
  → debounce 2s → stability check (size + mtime unchanged)
        │
        ▼
Job enqueued in SQLite (status: queued)
        │
        ▼
Background Worker picks up job
  1. [5%]   Hash check — skip if file unchanged
  2. [15%]  Extract audio → 16kHz mono WAV (ffmpeg)
  3. [22%]  Read duration (ffmpeg probe)
  4. [45%]  Transcribe audio (Whisper distil-large-v3, VAD filtered)
  5. [50%]  Delete temp WAV
  6. [65%]  Summarize transcript (DistilBART, chunked 1024 tokens)
  7. [75%]  Save to SQLite (media record + transcript segments)
  8. [85%]  Save semantic embeddings to LanceDB (MiniLM, sentence-window chunking)
  9. [90%]  Save summary embedding to LanceDB
 10. [97%]  Index visual frames (CLIP, 1 frame / 2 sec, batch 50, thumbnails saved)
 11. [100%] Job marked done
```

For PDFs and notes, steps 2–5 are replaced with page/paragraph extraction respectively.

---

## Search: How Hybrid RRF Works

Every query runs **two retrieval strategies in parallel**, then merges them:

1. **Semantic Search** — embeds your query with MiniLM and finds nearest neighbors in LanceDB (top 40)
2. **Keyword Search** — full-text FTS5 search in SQLite (top 40)

Results are fused using **Reciprocal Rank Fusion (RRF)**:

```
score(doc) = Σ  1 / (k + rank_in_source)   where k = 60
```

The final ranked list can be filtered by:
- **Source type** (`video`, `pdf`, `note`)
- **Folder prefix** (workspace scoping)
- **Date range** (`added_at` from SQLite)
- **Minimum score** threshold

---

## Edge Cases & Robustness

| Scenario | How TOBU Handles It |
|---|---|
| File still being copied when detected | Stability check: waits for size + mtime to stop changing |
| Temp/partial files (`.tmp`, `.part`, `.crdownload`) | Filtered by suffix and name pattern before enqueueing |
| File deleted from vault | Records removed from SQLite + LanceDB + thumbnails cleaned up |
| Job crash mid-processing | Retry counter incremented; re-queued up to `max_retries`, then marked `failed` |
| Stale `running` jobs on startup | `reset_stale_running_jobs()` re-queues them at boot |
| CUDA unavailable at runtime | Automatically falls back to CPU for Whisper and CLIP |
| Model files missing | Raises `RuntimeError` with a message pointing to the onboarding flow |
| Video with no valid audio track | `extract_audio` returns `None`; job raises `RuntimeError` and is retried |
| Video with invalid / zero FPS | Logged and skipped in `visual_engine` |
| Same file re-added unchanged | SHA-256 hash check detects no change; job marked `skipped_unchanged` |
| Duplicate job for same path | `enqueue_job` is idempotent; returns existing job ID |
| Empty transcript / document | Guarded with early return — "No valid segments" logged |

---

## API Reference

The backend exposes a versioned REST API at `http://127.0.0.1:8000/api/v1/`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check (DB reachability) |
| `GET` | `/system/status` | System info, job counts, model states |
| `GET` | `/system/models/status` | Per-model download status |
| `POST` | `/system/models/download` | Trigger background model download |
| `GET` | `/system/onboarding-status` | Check if first-launch setup is complete |
| `POST` | `/system/onboarding-completed` | Mark onboarding finished |
| `GET` | `/system/file-tree` | Directory tree of the watch folder |
| `GET` | `/system/browse-file` | Open native OS file picker |
| `GET` | `/system/browse-folder` | Open native OS folder picker |
| `DELETE` | `/system/workspace-folder` | Remove folder from index (disk untouched) |
| `POST` | `/system/cancel-indexing` | Cancel queued jobs for a folder |
| `GET` | `/system/integrity` | Run DB integrity check |
| `POST` | `/system/backup` | Create a labeled backup |
| `GET` | `/search` | Hybrid search (`q`, `limit`, `source_types`, `date_from`, `date_to`) |
| `POST` | `/ingest` | Manually enqueue a file for indexing |
| `GET` | `/jobs` | List all indexing jobs with status + progress |
| `GET` | `/media/{id}` | Fetch full transcript and metadata for a file |

All responses follow a consistent envelope:
```json
{ "ok": true,  "data": { ... } }
{ "ok": false, "error": { "code": "...", "message": "..." } }
```

---

## Project Structure

```
TOBU/
├── backend/
│   └── search_and_index/
│       ├── api_app.py            # FastAPI app + lifespan (worker + watcher startup)
│       ├── api_routes_*.py       # Route handlers (search, jobs, ingest, media, system)
│       ├── aural_engine.py       # Whisper transcription + ffmpeg audio extraction
│       ├── visual_engine.py      # CLIP frame embedding + thumbnail generation
│       ├── semantic_engine.py    # MiniLM embeddings + LanceDB vector store
│       ├── document_engine.py    # PDF (PyMuPDF) + Markdown/TXT processing
│       ├── summarizer.py         # DistilBART summarization
│       ├── runtime_service.py    # Worker loop + hybrid RRF search
│       ├── sql_database.py       # SQLite schema, job queue, FTS5 search
│       ├── watch.py              # Watchdog filesystem observer + debouncer
│       ├── model_downloader.py   # Model download + path management
│       └── requirements.txt
├── client/                       # React + Vite frontend
│   └── src/
│       ├── pages/                # Search, Jobs, Ingest, System
│       └── components/
├── desktop/                      # Electron shell
│   ├── main.js                   # Spawns backend, loads UI
│   └── preload.js
├── models/                       # Local AI model weights (git-ignored)
├── data/                         # SQLite DB, LanceDB vectors, thumbnails
├── watch/                        # Default vault drop folder
├── scripts/
│   └── build_backend.py          # PyInstaller build script
├── build_tobu.ps1                # One-shot full build script (Windows)
└── tobu-server.spec              # PyInstaller spec file
```

---

## Roadmap

### Near-Term
- [ ] **Multi-vault support** — manage multiple named watch folders independently
- [ ] **In-app playback** — click a transcript segment to jump to that timestamp in an embedded video player
- [ ] **Visual search from image** — drag-and-drop an image to find visually similar frames across all indexed videos
- [ ] **Re-index on demand** — force re-processing of a file even when hash is unchanged
- [ ] **Search filters in UI** — expose source type, date range, and folder filters in the frontend

### Medium-Term
- [ ] **Audio file support** — index `.mp3`, `.m4a`, `.wav` without video
- [ ] **GPU progress reporting** — live VRAM usage in the System panel
- [ ] **Export results** — save search results and transcripts to Markdown
- [ ] **macOS and Linux installers** — finalize cross-platform packaging with electron-builder
- [ ] **Configurable watch folders** — add/remove vault folders from within the UI

### Long-Term
- [ ] **Local LLM integration** — RAG-style Q&A over your vault using a local LLM (Ollama / llama.cpp)
- [ ] **Speaker diarization** — identify and label different speakers in a recording
- [ ] **OCR support** — index text from scanned PDFs and images
- [ ] **Mobile companion** — remote search via a local network endpoint
- [ ] **Plugin system** — allow custom ingestion engines for new file types

---

## Credits & Acknowledgements

TOBU is built on the shoulders of outstanding open-source projects:

| Project | Role |
|---|---|
| [**Faster-Whisper**](https://github.com/SYSTRAN/faster-whisper) by SYSTRAN | Efficient CTranslate2-based Whisper inference |
| [**sentence-transformers**](https://github.com/UKPLab/sentence-transformers) by UKPLab | MiniLM semantic embeddings + CLIP visual embeddings |
| [**LanceDB**](https://github.com/lancedb/lancedb) | Embedded vector database for semantic search |
| [**FastAPI**](https://github.com/tiangolo/fastapi) by Sebastián Ramírez | High-performance async API framework |
| [**Uvicorn**](https://github.com/encode/uvicorn) | ASGI server |
| [**ffmpeg-python**](https://github.com/kkroening/ffmpeg-python) | Python bindings for FFmpeg |
| [**PyMuPDF (fitz)**](https://github.com/pymupdf/PyMuPDF) | PDF text extraction |
| [**OpenCV**](https://opencv.org/) | Video frame extraction |
| [**Watchdog**](https://github.com/gorakhargosh/watchdog) | Filesystem event monitoring |
| [**Hugging Face Transformers**](https://github.com/huggingface/transformers) | DistilBART summarization |
| [**Electron**](https://electronjs.org/) | Cross-platform desktop shell |
| [**Vite**](https://vitejs.dev/) + [**React**](https://react.dev/) | Frontend tooling and UI framework |
| [**PyInstaller**](https://pyinstaller.org/) | Python app bundling |
| [**python-frontmatter**](https://github.com/eyeseast/python-frontmatter) | YAML front-matter parsing for Markdown |



---

## License

MIT License — see [LICENSE](LICENSE) for details.

---
## Authors


- [Vishnupiriyan V](https://github.com/VishnupiriyanV)
- [S Kavinikitha](https://github.com/s-kavinikitha)
- [Vishal M](https://github.com/Valiant-Vishal)
- [Nishanth S](https://github.com/NishanthGit3)

<div align="center">
<sub>Built with ❤️ and passion.</sub>
</div>
