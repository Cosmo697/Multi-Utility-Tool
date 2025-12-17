"""File organizer processing utilities."""
import os
import hashlib
import sqlite3
import shutil
import logging
from typing import Iterable, Dict, List

logger = logging.getLogger(__name__)

CACHE_DB = "file_cache.db"


def _get_db(db_path: str = CACHE_DB):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS hashes (path TEXT PRIMARY KEY, mtime REAL, size INTEGER, hash TEXT)"
    )
    return conn


def compute_hash(file_path: str, conn=None) -> str:
    """Return md5 hash of file, using cache if available."""
    if conn is None:
        conn = _get_db()
    mtime = os.path.getmtime(file_path)
    size = os.path.getsize(file_path)
    cur = conn.execute(
        "SELECT hash FROM hashes WHERE path=? AND mtime=? AND size=?",
        (file_path, mtime, size),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hash_md5.update(chunk)
    digest = hash_md5.hexdigest()
    conn.execute(
        "REPLACE INTO hashes(path, mtime, size, hash) VALUES (?,?,?,?)",
        (file_path, mtime, size, digest),
    )
    conn.commit()
    return digest


def _get_files(paths: Iterable[str], recursive: bool) -> List[str]:
    """Yield all files under the given paths."""
    found = []
    for p in paths:
        if os.path.isfile(p):
            found.append(p)
        elif os.path.isdir(p):
            if recursive:
                for root, _, files in os.walk(p):
                    for f in files:
                        found.append(os.path.join(root, f))
            else:
                for f in os.listdir(p):
                    fp = os.path.join(p, f)
                    if os.path.isfile(fp):
                        found.append(fp)
    return found


def scan_for_duplicates(
    paths: Iterable[str],
    recursive: bool = True,
    use_hash: bool = True,
    fuzzy: bool = False,
    conn=None,
) -> Dict[str, List[str]]:
    """Return mapping of hash/size key to list of duplicate file paths."""
    if conn is None:
        conn = _get_db()
    files = _get_files(paths, recursive)
    groups: Dict[str, List[str]] = {}
    for fp in files:
        try:
            size = os.path.getsize(fp)
        except OSError as exc:
            logger.error("Failed to stat %s: %s", fp, exc)
            continue
        key = str(size)
        if use_hash:
            try:
                key = compute_hash(fp, conn)
            except Exception as exc:
                logger.error("Hash failed for %s: %s", fp, exc)
                continue
        groups.setdefault(key, []).append(fp)

    # Filter out singletons
    dupes = {k: v for k, v in groups.items() if len(v) > 1}
    if fuzzy:
        # Very naive fuzzy matching based on file names ignoring extension
        name_map: Dict[str, List[str]] = {}
        for fp in files:
            base = os.path.splitext(os.path.basename(fp))[0].lower()
            name_map.setdefault(base, []).append(fp)
        for k, v in name_map.items():
            if len(v) > 1:
                dupes.setdefault(f"fuzzy:{k}", []).extend(v)
    return dupes


def move_files(files: Iterable[str], target_dir: str, delete: bool = False) -> None:
    os.makedirs(target_dir, exist_ok=True)
    for fp in files:
        name = os.path.basename(fp)
        dest = os.path.join(target_dir, name)
        shutil.copy2(fp, dest)
        if delete:
            os.remove(fp)
            logger.info("Moved and deleted %s", fp)
        else:
            logger.info("Copied %s", fp)


def delete_files(files: Iterable[str]) -> None:
    for fp in files:
        try:
            os.remove(fp)
            logger.info("Deleted %s", fp)
        except Exception as exc:
            logger.error("Failed to delete %s: %s", fp, exc)
