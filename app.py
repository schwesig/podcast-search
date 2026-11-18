"""Flask web UI for podcast transcript search."""
from flask import Flask, render_template_string, request, jsonify
import config
import searcher

app = Flask(__name__)

_HTML = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Podcast Search</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 1rem 1.5rem; background: #111; color: #eee; }
  h1 { font-size: 1.4rem; margin-bottom: 1rem; color: #adf; }
  form { display: flex; gap: .5rem; margin-bottom: 1.5rem; }
  input[type=text] { flex: 1; padding: .6rem .9rem; border-radius: 6px; border: 1px solid #444; background: #222; color: #eee; font-size: 1rem; }
  button { padding: .6rem 1.2rem; border-radius: 6px; border: none; background: #2a7fff; color: #fff; font-size: 1rem; cursor: pointer; }
  button:hover { background: #1a6fee; }
  .result { border: 1px solid #333; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; background: #1a1a1a; }
  .result h2 { font-size: 1rem; margin: 0 0 .3rem; }
  .result .meta { font-size: .8rem; color: #888; margin-bottom: .6rem; }
  .snippet { font-size: .9rem; color: #ccc; margin-bottom: .6rem; line-height: 1.5; }
  mark { background: #ff0; color: #000; border-radius: 2px; padding: 0 2px; }
  .segments { margin-top: .5rem; }
  .seg { display: inline-block; margin: .2rem .3rem .2rem 0; }
  .seg a { color: #7cf; text-decoration: none; font-size: .85rem; background: #1e3a5f; padding: .2rem .5rem; border-radius: 4px; }
  .seg a:hover { background: #2a5a8f; }
  .abs-link { font-size: .85rem; color: #adf; text-decoration: none; }
  .abs-link:hover { text-decoration: underline; }
  .no-results { color: #888; }
  #status { color: #888; font-size: .9rem; margin-bottom: 1rem; }
</style>
</head>
<body>
<h1>Podcast Search</h1>
<form id="f">
  <input type="text" id="q" name="q" placeholder="Suchbegriff..." value="{{ query }}" autofocus>
  <button type="submit">Suchen</button>
</form>
<div id="status"></div>
<div id="results">
{% if query and not results %}
  <p class="no-results">Keine Ergebnisse für "{{ query }}".</p>
{% endif %}
{% for r in results %}
<div class="result">
  <h2>{{ r.podcast }} &mdash; {{ r.title }}</h2>
  <div class="meta">{{ r.date }}
    {% if r.abs_url %}&nbsp;&bull;&nbsp;<a class="abs-link" href="{{ r.abs_url }}" target="_blank">In Audiobookshelf öffnen &rarr;</a>{% endif %}
  </div>
  <div class="snippet">{{ r.text_snippet | safe }}</div>
  {% if r.matched_segments %}
  <div class="segments">
    <span style="font-size:.8rem;color:#888">Timestamps:</span>
    {% for seg in r.matched_segments %}
    <span class="seg"><a href="{{ r.abs_url }}" title="{{ seg.text }}" target="_blank">{{ seg.timestamp }}</a></span>
    {% endfor %}
  </div>
  {% endif %}
</div>
{% endfor %}
</div>
<script>
document.getElementById('f').addEventListener('submit', async e => {
  e.preventDefault();
  const q = document.getElementById('q').value.trim();
  if (!q) return;
  document.getElementById('status').textContent = 'Suche…';
  const r = await fetch('/search?q=' + encodeURIComponent(q));
  const data = await r.json();
  document.getElementById('status').textContent = data.hits.length + ' Treffer';
  document.getElementById('results').innerHTML = data.hits.length === 0
    ? '<p class="no-results">Keine Ergebnisse.</p>'
    : data.hits.map(renderHit).join('');
  history.replaceState(null, '', '?q=' + encodeURIComponent(q));
});

function renderHit(r) {
  const segs = (r.matched_segments || []).map(s =>
    `<span class="seg"><a href="${r.abs_url}" title="${esc(s.text)}" target="_blank">${s.timestamp}</a></span>`
  ).join('');
  return `<div class="result">
    <h2>${esc(r.podcast)} &mdash; ${esc(r.title)}</h2>
    <div class="meta">${esc(r.date)}${r.abs_url ? ' &bull; <a class="abs-link" href="' + r.abs_url + '" target="_blank">In Audiobookshelf öffnen &rarr;</a>' : ''}</div>
    <div class="snippet">${r.text_snippet}</div>
    ${segs ? '<div class="segments"><span style="font-size:.8rem;color:#888">Timestamps:</span> ' + segs + '</div>' : ''}
  </div>`;
}
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
</script>
</body>
</html>"""


@app.route("/")
def index():
    query = request.args.get("q", "").strip()
    results = searcher.search(query) if query else []
    return render_template_string(_HTML, query=query, results=results)


@app.route("/search")
def search_api():
    query = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 20)), 100)
    if not query:
        return jsonify({"hits": []})
    return jsonify({"hits": searcher.search(query, limit)})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=False)
