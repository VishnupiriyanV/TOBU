import os
import sys
import time
import signal
import sqlite3
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]  # TOBU root
WATCH_FOLDER = str((ROOT_DIR / "watch").resolve())

RUNNING = True
PROCS = {}

def health_check():
    try:
        db_path = ROOT_DIR / "data" / "database" / "brain.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("SELECT 1")
        return True, "ok"
    except Exception as e:
        return False, str(e)

def _spawn(name, args):
    return subprocess.Popen(
        [sys.executable, "-u", *args],  
        cwd=str(BASE_DIR),
        stdout=None,   
        stderr=None,   
        text=True,
    )

def start_children():
    PROCS["worker"] = _spawn("worker", ["main.py", "--mode", "worker"])
    PROCS["watcher"] = _spawn("watcher", ["watch.py", "--folder", WATCH_FOLDER])

def stop_children():
    for _, p in PROCS.items():
        if p and p.poll() is None:
            p.terminate()
    deadline = time.time() + 5
    for _, p in PROCS.items():
        if not p:
            continue
        while p.poll() is None and time.time() < deadline:
            time.sleep(0.1)
        if p.poll() is None:
            p.kill()

def restart_if_dead():
    for name, p in list(PROCS.items()):
        if p and p.poll() is not None:
            print(f"[supervisor] {name} exited with code {p.returncode}, restarting...")
            if name == "worker":
                PROCS[name] = _spawn("worker", ["main.py", "--mode", "worker"])
            elif name == "watcher":
                PROCS[name] = _spawn("watcher", ["watch.py", "--folder", WATCH_FOLDER])

def _handle_signal(sig, frame):
    global RUNNING
    RUNNING = False

def main():
    global RUNNING

    ok, msg = health_check()
    if not ok:
        print(f"[supervisor] health check failed: {msg}")
        return

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print("[supervisor] starting worker + watcher")
    start_children()

    try:
        while RUNNING:
            restart_if_dead()
            time.sleep(1.0)
    finally:
        print("[supervisor] shutting down")
        stop_children()
        print("[supervisor] stopped")

if __name__ == "__main__":
    main()