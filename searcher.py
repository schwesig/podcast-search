"""Query Meilisearch and return results with timestamp context."""
import meilisearch
import config


def search(query: str, limit: int = 20) -> list[dict]:
    client = meilisearch.Client(config.MEILI_URL, config.MEILI_KEY)
    idx = client.index(config.MEILI_INDEX)

    result = idx.search(query, {
        "limit": limit,
        "attributesToHighlight": ["text", "title"],
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
        "attributesToCrop": ["text"],
        "cropLength": 200,
    })

    hits = []
    for hit in result.get("hits", []):
        segments = hit.get("segments", [])
        # Find segments that contain the query terms
        matched_segments = _find_matching_segments(query, segments)

        hits.append({
            "id": hit.get("id"),
            "podcast": hit.get("podcast", ""),
            "title": hit.get("title", ""),
            "date": hit.get("date", ""),
            "text_snippet": hit.get("_formatted", {}).get("text", hit.get("text", ""))[:300],
            "matched_segments": matched_segments,
            "abs_url": hit.get("abs_url", ""),
            "episode_dir": hit.get("episode_dir", ""),
        })

    return hits


def _find_matching_segments(query: str, segments: list[dict]) -> list[dict]:
    """Return segments whose text contains any query word, with timestamps."""
    if not segments:
        return []
    words = [w.lower() for w in query.split() if len(w) > 2]
    if not words:
        return []

    matches = []
    for seg in segments:
        text_lower = seg.get("text", "").lower()
        if any(w in text_lower for w in words):
            matches.append({
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", ""),
                "timestamp": _fmt_time(seg.get("start", 0)),
            })
    return matches[:5]  # top 5 segment matches per episode


def _fmt_time(seconds: float) -> str:
    s = int(seconds)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}:{m:02}:{s:02}"
    return f"{m}:{s:02}"
