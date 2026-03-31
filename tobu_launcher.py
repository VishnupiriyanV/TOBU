import os
import sys
import multiprocessing

# Add project root to sys.path to allow absolute imports
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)


def _stdio_stream_available(stream):
    return stream is not None and callable(getattr(stream, "isatty", None))


def _can_prompt_for_input():
    stdin = getattr(sys, "stdin", None)
    return _stdio_stream_available(stdin) and stdin.isatty()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Import the app using absolute import
    try:
        from backend.search_and_index.api_app import app
        import uvicorn
        print("[TOBU] Launcher starting backend...")

        uvicorn_kwargs = {}
        # PyInstaller/windowed launches may not have stdin/stderr streams.
        if not _stdio_stream_available(getattr(sys, "stderr", None)):
            uvicorn_kwargs["log_config"] = None
            uvicorn_kwargs["access_log"] = False

        uvicorn.run(app, host="127.0.0.1", port=8000, **uvicorn_kwargs)
    except Exception as e:
        print(f"[TOBU] Launcher Error: {e}")
        import traceback
        traceback.print_exc()
        if _can_prompt_for_input():
            input("Press Enter to close...")
