import sqlite3
import os
import hashlib
import time
import shutil
from datetime import datetime
import lancedb


MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
import sys
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(os.path.join(MODULE_DIR, "..", ".."))
DB_DIR = os.path.join(PROJECT_ROOT, "data", "database")
DATABASE_PATH = os.path.join(DB_DIR, "brain.db")
os.makedirs(DB_DIR, exist_ok=True)
VECTOR_DB_PATH = os.path.join(DB_DIR, "vector_data")
THUMBNAIL_PATH = os.path.join(PROJECT_ROOT, "data", "thumbnails")
RECENT_DUPLICATE_SECONDS = 12
#create table

def initialize_db():
    with sqlite3.connect(DATABASE_PATH) as connection:
        mediaFiles_create_table = """

        CREATE TABLE IF NOT EXISTS media_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        source_type TEXT DEFAULT 'video',  --'video','pdf','markdown','txt'
        duration_seconds REAL, -- NULL for non media
        summary TEXT,
        added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending', --pending,processing,indexed,error
        file_hash TEXT


        )

        """


        transcript_fts ="""

        CREATE VIRTUAL TABLE IF NOT EXISTS transcripts_fts USING fts5(
            media_id UNINDEXED ,
            location_start UNINDEXED,
            location_end UNINDEXED,
            content,
            file_name
            );
        """

        jobs_create_table = """
        CREATE TABLE IF NOT EXISTS indexing_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            source_type TEXT,
            status TEXT NOT NULL DEFAULT 'queued', -- queued,running,failed,done,cancelled
            stage TEXT NOT NULL DEFAULT 'pending',
            progress REAL NOT NULL DEFAULT 0,
            retries INTEGER NOT NULL DEFAULT 0,
            max_retries INTEGER NOT NULL DEFAULT 3,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """

        jobs_status_index = """
        CREATE INDEX IF NOT EXISTS idx_indexing_jobs_status_created
        ON indexing_jobs(status, created_at);
        """


        settings_create_table = """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """

        cursor = connection.cursor()

        try:
            cursor.execute(mediaFiles_create_table)
            cursor.execute(transcript_fts)
            cursor.execute(jobs_create_table)
            cursor.execute(jobs_status_index)
            cursor.execute(settings_create_table)
            
            # Initial onboarding status
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES ('onboarding_completed', 'false')")
            
            connection.commit()
        except Exception as e:
            print(f"Database init error: {e}")
            connection.rollback()

#initialize_db()

def get_media_id(file_path):
    """Get media_id for an existing file path."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        result = cursor.fetchone()
        return result[0] if result else None


#FOR SAVING TRANSCRIPT
def save_to_db(file_path, file_name, duration, transcript_data,source_type="video", summary=None, current_hash=None):
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    

    try:
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        existing_row = cursor.fetchone()
        if current_hash is None:
            current_hash = compute_file_hash(file_path)

        if existing_row is not None:
            media_id = existing_row[0]
            cursor.execute(
                """
                UPDATE media_files
                SET file_name = ?,
                    duration_seconds = ?,
                    source_type = ?,
                    summary = ?,
                    status = 'indexed',
                    file_hash = ?
                WHERE id = ?
                """,
                (file_name, duration, source_type, summary, current_hash, media_id),
            )
            cursor.execute("DELETE FROM transcripts_fts WHERE media_id = ?", (media_id,))
        else:
            insert_cmd = """INSERT INTO media_files (file_path,file_name,duration_seconds,source_type,status,summary,file_hash) VALUES (?,?,?,?,'indexed',?,?)"""
            cursor.execute(insert_cmd, (file_path, file_name, duration,source_type, summary,current_hash))
            media_id = cursor.lastrowid

        data_to_insert = (
            (
                media_id,
                seg['start'] if seg.get('start') is not None else seg.get('page'),
                seg['end'] if seg.get('end') is not None else seg.get('page'),
                seg['text'],
                file_name,
            )
            for seg in transcript_data
        )

        cursor.executemany("""
            INSERT INTO transcripts_fts (media_id, location_start, location_end, content, file_name)
            VALUES (?, ?, ?, ?, ?)
        """, data_to_insert)

        connection.commit()
        print(f"indexed: {file_name}")

        return media_id

    except Exception as e:
        print(f"Database Error:{e}")
        connection.rollback()
        return None

    finally:
        connection.close()


#for final json

def search_to_json(query):
    with sqlite3.connect(DATABASE_PATH) as connection:
        
        connection.row_factory = sqlite3.Row 
        cursor = connection.cursor()
        
        search_query = """
            SELECT 
                f.file_name, 
                f.file_path, 
                t.location_start, 
                t.location_end, 
                t.content as text,
                t.rank as score
            FROM transcripts_fts t
            JOIN media_files f ON t.media_id = f.id
            WHERE t.content MATCH ? 
            ORDER BY rank 
            LIMIT 50
        """
        
        query1 = f'"{query}"'
        cursor.execute(search_query, (query1,))
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            results.append({
                "file-name": row["file_name"],
                "file-path": os.path.abspath(row["file_path"]), 
                "start": row["location_start"],
                "end": row["location_end"],
                "text": row["text"],
                "score": row["score"]
                })
        

        return results

def compute_file_hash(path,chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with open(path,"rb") as f:
        chunk = f.read(chunk_size)
        while chunk:
            h.update(chunk)
            chunk = f.read(chunk_size)
    return h.hexdigest()


#return true if the file should be processed (not yet indexed, or hash has changed)
def should_process(file_path):
    if not os.path.exists(file_path):
        return False, None
        
    current_hash = compute_file_hash(file_path)
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute(
            "SELECT file_hash FROM media_files WHERE file_path = ?", (file_path,)
        ).fetchone()

    if row is None:
        return True, current_hash
    return row[0] != current_hash, current_hash

def delete_file_records(file_path):
    """Remove a file's records from media_files and transcripts_fts."""
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM media_files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        if row is None:
            return
        media_id = row[0]

        
        try:
            db = lancedb.connect(VECTOR_DB_PATH)
            for table_name in ("semantic_segments", "summary_segments", "visual_moments"):
                if table_name in db.table_names():
                    table = db.open_table(table_name)
                    table.delete(f"media_id = {int(media_id)}")
        except Exception as e:
            print(f"Vector cleanup error for {file_path}: {e}")

        
        if os.path.isdir(THUMBNAIL_PATH):
            prefix = f"{media_id}_"
            for name in os.listdir(THUMBNAIL_PATH):
                if name.startswith(prefix):
                    thumb_path = os.path.join(THUMBNAIL_PATH, name)
                    try:
                        os.remove(thumb_path)
                    except Exception:
                        pass

        cursor.execute("DELETE FROM transcripts_fts WHERE media_id = ?", (media_id,))
        cursor.execute("DELETE FROM media_files WHERE id = ?", (media_id,))
        connection.commit()
        print(f"Removed from index: {file_path}")

def remove_workspace_folder(folder_path):
    """Safely remove app data for all files prefixed with the folder path."""
    normalized = os.path.abspath(folder_path)
    prefix = normalized + os.sep
    
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, file_path FROM media_files WHERE file_path = ? OR file_path LIKE ?", (normalized, prefix + '%'))
        rows = cursor.fetchall()
        
        if not rows:
            return {"embeddings": 0, "transcripts": 0, "index_entries": 0}
            
        media_ids = [r[0] for r in rows]
        media_ids_str = ",".join(map(str, media_ids))
        
        cursor.execute(f"SELECT COUNT(*) FROM transcripts_fts WHERE media_id IN ({media_ids_str})")
        transcripts_count = cursor.fetchone()[0]
        
        index_entries_count = len(media_ids)
        embeddings_count = 0
        
        try:
            db = lancedb.connect(VECTOR_DB_PATH)
            for table_name in ("semantic_segments", "summary_segments", "visual_moments"):
                if table_name in db.table_names():
                    table = db.open_table(table_name)
                    # For metrics, we can query it first using an index/map or estimate. In LanceDB, count is not always O(1).
                    try:
                       res = table.search().where(f"media_id IN ({media_ids_str})")
                       if hasattr(res, 'to_arrow'):
                         embeddings_count += len(res.to_arrow())
                    except Exception:
                       pass # Fallback if search fails
                    table.delete(f"media_id IN ({media_ids_str})")
        except Exception as e:
            print(f"Vector cleanup error for {folder_path}: {e}")
            
        if os.path.isdir(THUMBNAIL_PATH):
            for m_id in media_ids:
                prefix_thumb = f"{m_id}_"
                for name in os.listdir(THUMBNAIL_PATH):
                    if name.startswith(prefix_thumb):
                        try:
                            os.remove(os.path.join(THUMBNAIL_PATH, name))
                        except Exception:
                            pass
                            
        cursor.execute(f"DELETE FROM transcripts_fts WHERE media_id IN ({media_ids_str})")
        cursor.execute(f"DELETE FROM media_files WHERE id IN ({media_ids_str})")
        
        cursor.execute("UPDATE indexing_jobs SET status = 'cancelled' WHERE file_path = ? OR file_path LIKE ?", (normalized, prefix + '%'))
        connection.commit()
        
        return {
            "embeddings": embeddings_count,
            "transcripts": transcripts_count,
            "index_entries": index_entries_count
        }

def save_doc_to_db(file_path, file_name, segments, source_type="note", summary=None, current_hash=None):
    return save_to_db(
        file_path,
        file_name,
        None,
        segments,
        source_type=source_type,
        summary=summary,
        current_hash=current_hash,
    )

def enqueue_job(file_path, source_type=None, max_retries=3):
    normalized_path = os.path.abspath(file_path)
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()

        
        cursor.execute(
            """
            SELECT id FROM indexing_jobs
            WHERE file_path = ? AND status IN ('queued', 'running')
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (normalized_path,),
        )
        exists = cursor.fetchone()
        if exists:
            return exists[0], False

        # for noisy repeated file-system events
        cursor.execute(
            """
            SELECT id FROM indexing_jobs
            WHERE file_path = ?
              AND created_at >= datetime('now', ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (normalized_path, f"-{int(RECENT_DUPLICATE_SECONDS)} seconds"),
        )
        recent = cursor.fetchone()
        if recent:
            return recent[0], False

        cursor.execute(
            """
            INSERT INTO indexing_jobs (file_path, source_type, status, stage, progress, max_retries)
            VALUES (?, ?, 'queued', 'pending', 0, ?)
            """,
            (normalized_path, source_type, max_retries),
        )
        connection.commit()
        return cursor.lastrowid, True

def fetch_next_job():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

       
        cursor.execute("BEGIN IMMEDIATE")

        cursor.execute(
            """
            SELECT id, file_path, source_type, retries, max_retries
            FROM indexing_jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if row is None:
            connection.commit()
            return None

        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'running',
                stage = 'starting',
                progress = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'queued'
            """,
            (row["id"],),
        )

        if cursor.rowcount != 1:
            connection.commit()
            return None

        connection.commit()
        return dict(row)
    
def update_job_status(job_id, status, stage=None, progress=None, error_message=None):
    fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
    params = [status]

    if stage is not None:
        fields.append("stage = ?")
        params.append(stage)
    if progress is not None:
        fields.append("progress = ?")
        params.append(progress)
    if error_message is not None:
        fields.append("error_message = ?")
        params.append(error_message)

    params.append(job_id)

    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE indexing_jobs SET {', '.join(fields)} WHERE id = ?",
            tuple(params),
        )
        connection.commit()

def increment_retry(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET retries = retries + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        connection.commit()

def get_job_retries(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT retries, max_retries FROM indexing_jobs WHERE id = ?",
            (job_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return 0, 0
        return row[0], row[1]


def requeue_job(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'queued',
                stage = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (job_id,),
        )
        connection.commit()

def reset_stale_running_jobs():
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'queued',
                stage = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'running'
            """
        )
        connection.commit()

def cancel_jobs_for_path(file_path):
    normalized_path = os.path.abspath(file_path)
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'cancelled',
                stage = 'cancelled',
                updated_at = CURRENT_TIMESTAMP
            WHERE file_path = ? AND status IN ('queued', 'running')
            """,
            (normalized_path,),
        )
        connection.commit()

def get_job(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, file_path, source_type, status, stage, progress, retries,
                   max_retries, error_message, created_at, updated_at
            FROM indexing_jobs
            WHERE id = ?
            """,
            (job_id,),
        ).fetchone()
        return dict(row) if row else None


def list_jobs(status=None, limit=100):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        if status:
            rows = connection.execute(
                """
                SELECT id, file_path, source_type, status, stage, progress, retries,
                       max_retries, error_message, created_at, updated_at
                FROM indexing_jobs
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, file_path, source_type, status, stage, progress, retries,
                       max_retries, error_message, created_at, updated_at
                FROM indexing_jobs
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


def retry_job(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'queued',
                stage = 'pending',
                progress = 0,
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status IN ('failed', 'cancelled')
            """,
            (job_id,),
        )
        connection.commit()
        return cursor.rowcount == 1


def cancel_job(job_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE indexing_jobs
            SET status = 'cancelled',
                stage = 'cancelled',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status IN ('queued', 'running')
            """,
            (job_id,),
        )
        connection.commit()
        return cursor.rowcount == 1


def get_media_detail(media_id):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT id, file_path, file_name, source_type, duration_seconds,
                   summary, added_at, status, file_hash
            FROM media_files
            WHERE id = ?
            """,
            (media_id,),
        ).fetchone()
        return dict(row) if row else None


def get_media_segments(media_id, limit=200):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT location_start AS start,
                   location_end AS end,
                   content AS text,
                   file_name
            FROM transcripts_fts
            WHERE media_id = ?
            LIMIT ?
            """,
            (media_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_db_stats():
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        media_count = cursor.execute("SELECT COUNT(*) FROM media_files").fetchone()[0]
        jobs_count = cursor.execute("SELECT COUNT(*) FROM indexing_jobs").fetchone()[0]
        queued = cursor.execute("SELECT COUNT(*) FROM indexing_jobs WHERE status = 'queued'").fetchone()[0]
        running = cursor.execute("SELECT COUNT(*) FROM indexing_jobs WHERE status = 'running'").fetchone()[0]
        failed = cursor.execute("SELECT COUNT(*) FROM indexing_jobs WHERE status = 'failed'").fetchone()[0]

    return {
        "media_files": media_count,
        "jobs_total": jobs_count,
        "jobs_queued": queued,
        "jobs_running": running,
        "jobs_failed": failed,
    }


def integrity_check():
    with sqlite3.connect(DATABASE_PATH) as connection:
        row = connection.execute("PRAGMA integrity_check;").fetchone()
        sqlite_ok = bool(row and row[0] == "ok")

    vector_tables = []
    vector_ok = True
    try:
        db = lancedb.connect(VECTOR_DB_PATH)
        vector_tables = sorted(db.table_names())
    except Exception:
        vector_ok = False

    return {
        "sqlite_integrity": "ok" if sqlite_ok else "fail",
        "vector_store": "ok" if vector_ok else "fail",
        "vector_tables": vector_tables,
        "database_path": DATABASE_PATH,
    }


def create_backup(label=None):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"backup_{label}_{ts}" if label else f"backup_{ts}"
    backup_root = os.path.join(PROJECT_ROOT, "data", "backups", name)
    os.makedirs(backup_root, exist_ok=True)

    db_dst = os.path.join(backup_root, "brain.db")
    if os.path.exists(DATABASE_PATH):
        shutil.copy2(DATABASE_PATH, db_dst)

    vector_dst = os.path.join(backup_root, "vector_data")
    if os.path.isdir(VECTOR_DB_PATH):
        shutil.copytree(VECTOR_DB_PATH, vector_dst, dirs_exist_ok=True)

    thumbs_dst = os.path.join(backup_root, "thumbnails")
    if os.path.isdir(THUMBNAIL_PATH):
        shutil.copytree(THUMBNAIL_PATH, thumbs_dst, dirs_exist_ok=True)

    return {
        "backup_path": backup_root,
        "database_copied": os.path.exists(db_dst),
        "vector_copied": os.path.isdir(vector_dst),
        "thumbnails_copied": os.path.isdir(thumbs_dst),
    }

def get_setting(key, default=None):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

def set_setting(key, value):
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO app_settings (key, value) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
        connection.commit()