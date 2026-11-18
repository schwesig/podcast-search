# podcast-search

Indexes podcast transcripts from [podcast-transcriber](https://github.com/schwesig/podcast-transcriber) into Meilisearch and provides a web UI with full-text search and timestamp links back to Audiobookshelf.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in MEILI_KEY and ABS_KEY
```

## Index transcripts

```bash
python indexer.py
# or point at a specific dir:
python indexer.py --dir /opt/podcast-transcriber/podcasts
```

## Run web UI

```bash
python app.py
# opens on http://localhost:8300
```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MEILI_URL` | `http://100.78.89.30:8250` | Meilisearch URL |
| `MEILI_KEY` | — | Meilisearch master key |
| `MEILI_INDEX` | `podcasts` | Index name |
| `ABS_URL` | `http://100.78.89.30:8240` | Audiobookshelf URL |
| `ABS_KEY` | — | ABS API key |
| `TRANSCRIPTS_DIR` | `/opt/podcast-transcriber/podcasts` | Transcripts root |
| `PORT` | `8300` | Web UI port |
