import os
import sys
import time
import signal
import sqlite3
import subprocess
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(os.path.expanduser("~/.tobu"))
    ROOT_DIR.mkdir(parents=True, exist_ok=True)
else:
    ROOT_DIR = BASE_DIR.parents[1]  # TOBU root
WATCH_FOLDER = str((ROOT_DIR / "watch").resolve())
LOG_DIR = ROOT_DIR / "data" / "logs"
SUPERVISOR_LOG = LOG_DIR / "supervisor.log"

RUNNING = True
PROCS = {}


def _log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SUPERVISOR_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _preflight_checks():
    (ROOT_DIR / "data" / "database").mkdir(parents=True, exist_ok=True)
    (ROOT_DIR / "data" / "thumbnails").mkdir(parents=True, exist_ok=True)
    Path(WATCH_FOLDER).mkdir(parents=True, exist_ok=True)
    if not (BASE_DIR / "main.py").exists():
        raise RuntimeError("Missing main.py in backend/search_and_index")
    if not (BASE_DIR / "watch.py").exists():
        raise RuntimeError("Missing watch.py in backend/search_and_index")

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


def _is_expected_exit(returncode):
    # 
    # 0 - clean exit
    # 1 -  scripts exit 1 on KeyboardInterrupt
    # 130 = SIGINT-style exit code on Unix-like conventions
    return returncode in (0, 1, 130)


def _classify_exit(name, returncode):
    if not RUNNING and _is_expected_exit(returncode):
        return "expected_shutdown"
    if _is_expected_exit(returncode):
        return "possible_manual_interrupt"
    return "crash"

def start_children():
    PROCS["worker"] = _spawn("worker", ["main.py", "--mode", "worker"])
    PROCS["watcher"] = _spawn("watcher", ["watch.py", "--folder", WATCH_FOLDER])
    _log("started child processes: worker, watcher")

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
    _log("all child processes stopped")

def restart_if_dead():
    for name, p in list(PROCS.items()):
        if p and p.poll() is not None:
            exit_type = _classify_exit(name, p.returncode)
            if exit_type == "expected_shutdown":
                _log(f"{name} exited with code {p.returncode} (expected during shutdown)")
                continue

            if exit_type == "possible_manual_interrupt":
                _log(f"{name} exited with code {p.returncode} (manual interrupt or controlled stop)")
                if not RUNNING:
                    continue

            if exit_type == "crash":
                _log(f"{name} exited with code {p.returncode} (crash), restarting")
            else:
                _log(f"{name} exited with code {p.returncode}, restarting")

            if name == "worker":
                PROCS[name] = _spawn("worker", ["main.py", "--mode", "worker"])
            elif name == "watcher":
                PROCS[name] = _spawn("watcher", ["watch.py", "--folder", WATCH_FOLDER])

def _handle_signal(sig, frame):
    global RUNNING
    RUNNING = False

def main():
    _preflight_checks()
    ok, msg = health_check()
    if not ok:
        _log(f"health check failed: {msg}")
        return

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    _log("starting worker + watcher")
    start_children()

    try:
        while RUNNING:
            restart_if_dead()
            time.sleep(1.0)
    except Exception as e:
        _log(f"supervisor exception: {e}")
        _log(traceback.format_exc())
        raise
    finally:
        _log("shutting down")
        stop_children()
        _log("stopped")

if __name__ == "__main__":
    main()