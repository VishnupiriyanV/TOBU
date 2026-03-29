import os
import subprocess
import sys

def main():
    print("Building TOBU Backend with PyInstaller...")

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    api_app_path = os.path.join(project_root, "tobu_launcher.py")

    hidden_imports = [
        "backend.search_and_index.sql_database",
        "backend.search_and_index.runtime_service",
        "backend.search_and_index.watch",
        "uvicorn",
        "fastapi",
        "chromadb",
        "sqlite3",
        "sentence_transformers",
        "faster_whisper",
        "torch",
        "lancedb",
        "python-multipart"
    ]

    args = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "tobu-vault-engine",
    ]

    for h in hidden_imports:
        args.extend(["--hidden-import", h])

    # We need to add the backend folder to PYTHONPATH basically so it can be imported
    args.extend([
        "--paths", project_root,
        api_app_path
    ])

    print("Running command:", " ".join(args))
    subprocess.check_call(args, cwd=project_root)
    print("Build complete!")

if __name__ == "__main__":
    main()
