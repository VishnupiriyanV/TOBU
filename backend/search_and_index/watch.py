from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from main import process_media
from sql_database import initialize_db, delete_file_records
import os
import time
import sys

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".pdf", ".md", ".txt"}

class FileHandler(FileSystemEventHandler):
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
                delete_file_records(event.src_path)
            except Exception as e:
                print(f"Error removing {event.src_path}: {e}")

    def _handle(self, path):
        ext = os.path.splitext(path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return
        time.sleep(2)
        try:
            process_media(path)
        except Exception as e:
            print(f"Error processing {path}: {e}")
    
def initial_scan(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            path = os.path.join(root, f)
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                try:
                    process_media(path)
                except Exception as e:
                    print(f"Error processing {path}: {e}")


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
    watch_folder = "watch_folder"
    start_watcher(watch_folder)