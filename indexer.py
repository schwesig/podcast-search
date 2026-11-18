"""Read transcript files and index them into Meilisearch."""
import json
import sys
from pathlib import Path

import meilisearch

import config


def _load_episode(ep_dir: Path) -> dict | None:
    """Build a Meilisearch document from one episode directory."""
    # find the dated slug — the stem shared by all files
    txt_files = list(ep_dir.glob("*.txt"))
    if not txt_files:
        return None
    stem = txt_files[0].stem

    txt_path = ep_dir / f"{stem}.txt"
    json_path = ep_dir / f"{stem}.json"
    meta_path = ep_dir / "metadata.json"

    text = txt_path.read_text(errors="replace").strip() if txt_path.exists() else ""
    if not text:
        return None

    segments = []
    if json_path.exists():
        try:
            segments = json.loads(json_path.read_text())
        except Exception:
            pass

    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            pass

    feed_slug = ep_dir.parent.name
    doc_id = f"{feed_slug}__{stem}"

    return {
        "id": doc_id,
        "feed_slug": feed_slug,
        "episode_slug": stem,
        "podcast": meta.get("podcast", feed_slug),
        "title": meta.get("title", stem),
        "date": meta.get("date", ""),
        "duration": meta.get("duration", ""),
        "summary": meta.get("summary", ""),
        "text": text,
        "segments": segments,  # [{start, end, text}, ...]
        "episode_dir": str(ep_dir),
    }


def _abs_deeplink(doc: dict) -> str:
    """Build an Audiobookshelf deep link for this episode if possible."""
    # ABS podcast search by title is the best we can do without ABS episode IDs
    title = doc.get("title", "")
    if not title:
        return ""
    import urllib.parse
    return f"{config.ABS_URL}/podcasts?search={urllib.parse.quote(title)}"


def index_all(transcripts_dir: str = None, dry_run: bool = False) -> int:
    root = Path(transcripts_dir or config.TRANSCRIPTS_DIR)
    if not root.exists():
        print(f"Transcripts dir not found: {root}", file=sys.stderr)
        return 0

    client = meilisearch.Client(config.MEILI_URL, config.MEILI_KEY)
    idx = client.index(config.MEILI_INDEX)

    # Configure searchable and filterable attributes once
    idx.update_searchable_attributes(["title", "podcast", "text", "summary"])
    idx.update_filterable_attributes(["feed_slug", "podcast", "date"])
    idx.update_sortable_attributes(["date"])

    docs = []
    for ep_dir in sorted(root.glob("*/*")):
        if not ep_dir.is_dir():
            continue
        doc = _load_episode(ep_dir)
        if doc is None:
            continue
        doc["abs_url"] = _abs_deeplink(doc)
        docs.append(doc)

    if not docs:
        print("No episodes found to index.")
        return 0

    if dry_run:
        print(f"Would index {len(docs)} episodes (dry run).")
        return len(docs)

    # Batch in chunks of 100
    total = 0
    for i in range(0, len(docs), 100):
        batch = docs[i:i + 100]
        idx.add_documents(batch)
        total += len(batch)
        print(f"  Indexed {total}/{len(docs)}...")

    print(f"Done. {total} episodes indexed into '{config.MEILI_INDEX}'.")
    return total


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Index podcast transcripts into Meilisearch")
    parser.add_argument("--dir", help="Transcripts directory (overrides config)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    index_all(args.dir, args.dry_run)
