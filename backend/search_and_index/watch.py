from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sql_database import initialize_db, delete_file_records, enqueue_job, cancel_jobs_for_path
import os
import time
import argparse

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".pdf", ".md", ".txt"}
TEMP_SUFFIXES = (".tmp", ".part", ".partial", ".crdownload", ".swp", ".swx", "~")
TEMP_NAMES = {"thumbs.db", ".ds_store"}


class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._last_event_time = {}
        self._debounce_seconds = 2.0
        self._stability_wait_seconds = 1.2
        self._stability_checks = 2

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        ext = os.path.splitext(event.src_path)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            try:
                cancel_jobs_for_path(event.src_path)
                delete_file_records(event.src_path)
            except Exception as e:
                print(f"Error removing {event.src_path}: {e}")

    def _is_temporary_file(self, path):
        name = os.path.basename(path).lower()
        if name in TEMP_NAMES:
            return True
        if name.startswith(".~") or name.startswith("~$"):
            return True
        if any(name.endswith(sfx) for sfx in TEMP_SUFFIXES):
            return True
        return False

    def _is_file_stable(self, path):
        # Returns True only if size m time remain unchanged for n checks.
        if not os.path.exists(path):
            return False

        try:
            prev_size = os.path.getsize(path)
            prev_mtime = os.path.getmtime(path)
        except OSError:
            return False

        if prev_size <= 0:
            return False
        #checks before and after size are same
        for _ in range(self._stability_checks):
            time.sleep(self._stability_wait_seconds)
            if not os.path.exists(path):
                return False
            try:
                cur_size = os.path.getsize(path)
                cur_mtime = os.path.getmtime(path)
            except OSError:
                return False

            if cur_size != prev_size or cur_mtime != prev_mtime:
                return False

            prev_size = cur_size
            prev_mtime = cur_mtime

        return True

    def _handle(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        if self._is_temporary_file(path):
            return

        now = time.time()
        last = self._last_event_time.get(path, 0.0)
        if now - last < self._debounce_seconds:
            return
        self._last_event_time[path] = now

        if not os.path.exists(path):
            return

        if not self._is_file_stable(path):
            return

        source_type = {
            ".pdf": "pdf",
            ".md": "note",
            ".txt": "note",
        }.get(ext, "video")

        job_id, created = enqueue_job(path, source_type=source_type)
        if created:
            print(f"Queued job {job_id}: {path}")


def initial_scan(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                if not os.path.exists(path):
                    continue
                source_type = {
                    ".pdf": "pdf",
                    ".md": "note",
                    ".txt": "note",
                }.get(ext, "video")
                try:
                    enqueue_job(path, source_type=source_type)
                except Exception as e:
                    print(f"Error queueing {path}: {e}")


def start_watcher(folder):
    initialize_db()
    print(f"Initial scan on: {folder}")
    initial_scan(folder)
    print(f"Watching for changes in: {folder}")

    observer = Observer()
    observer.schedule(FileHandler(), folder, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Watcher stopped.")
    observer.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", type=str, default="watch")
    args = parser.parse_args()
    start_watcher(args.folder)

    