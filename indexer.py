"""Read transcript files and index them into Meilisearch."""
import json
import sys
from pathlib import Path

import meilisearch

import config


def _parse_srt(srt_path: Path) -> list[dict]:
    """Parse an SRT file into [{start, end, text}, ...] with float seconds."""
    segments = []
    if not srt_path.exists():
        return segments
    block, start, end = [], None, None
    for line in srt_path.read_text(errors="replace").splitlines():
        line = line.strip()
        if "-->" in line:
            parts = line.split("-->")
            start = _srt_to_sec(parts[0].strip())
            end = _srt_to_sec(parts[1].strip())
        elif line and not line.isdigit() and start is not None:
            block.append(line)
        elif not line and block:
            segments.append({"start": start, "end": end, "text": " ".join(block)})
            block, start, end = [], None, None
    if block and start is not None:
        segments.append({"start": start, "end": end, "text": " ".join(block)})
    return segments


def _srt_to_sec(ts: str) -> float:
    """'00:01:23,456' -> 83.456"""
    ts = ts.replace(",", ".")
    parts = ts.split(":")
    try:
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0


def _load_episode(ep_dir: Path) -> dict | None:
    """Build a Meilisearch document from one episode directory."""
    txt_files = list(ep_dir.glob("*.txt"))
    if not txt_files:
        return None
    stem = txt_files[0].stem

    txt_path = ep_dir / f"{stem}.txt"
    # podcast-transcriber writes metadata (podcast/title/date/summary) into <stem>.json
    json_path = ep_dir / f"{stem}.json"
    srt_path = ep_dir / f"{stem}.srt"

    text = txt_path.read_text(errors="replace").strip() if txt_path.exists() else ""
    if not text:
        return None

    # Segments from SRT (timestamp-accurate, even if currently one big block)
    segments = _parse_srt(srt_path)

    meta = {}
    if json_path.exists():
        try:
            meta = json.loads(json_path.read_text())
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
