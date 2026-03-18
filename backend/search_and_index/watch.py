from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sql_database import initialize_db, delete_file_records, enqueue_job, cancel_jobs_for_path
import os
import time

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".pdf", ".md", ".txt"}

class FileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._last_event_time = {}
        self._debounce_seconds = 2.0

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

    def _handle(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return

        now = time.time()
        last = self._last_event_time.get(path, 0)
        if now - last < self._debounce_seconds:
            return
        self._last_event_time[path] = now

        if not os.path.exists(path):
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
    print(f"initial scan on: {folder}")
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
    watch_folder = "watch"
    start_watcher(watch_folder)