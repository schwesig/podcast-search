import os

# Meilisearch
MEILI_URL = os.environ.get("MEILI_URL", "http://100.78.89.30:8250")
MEILI_KEY = os.environ.get("MEILI_KEY", "")
MEILI_INDEX = os.environ.get("MEILI_INDEX", "podcasts")

# Audiobookshelf
ABS_URL = os.environ.get("ABS_URL", "http://100.78.89.30:8240")
ABS_KEY = os.environ.get("ABS_KEY", "")

# Transcripts root (where podcast-transcriber writes output)
TRANSCRIPTS_DIR = os.environ.get("TRANSCRIPTS_DIR", "/opt/podcast-transcriber/podcasts")

# Web UI
PORT = int(os.environ.get("PORT", "8300"))
