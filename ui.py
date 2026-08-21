import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from genes import Genome
from TenderFace import generate_face_svg

PORT = 8765

# Server-side parent state — persists across requests within one server session.
parent_genomes = [Genome(num_genes=200), Genome(num_genes=200)]


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tender Face Generator</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: sans-serif;
      background: #f5f5f0;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px 24px;
      gap: 28px;
    }
    h1 { margin: 0; font-size: 1.4rem; color: #333; }

    .section {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      width: 100%;
    }
    .section-label {
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: #888;
      align-self: flex-start;
      max-width: 560px;
      width: 100%;
    }

    .parents-row {
      display: flex;
      gap: 24px;
      justify-content: center;
    }
    .parent-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
    }

    .children-row {
      display: flex;
      gap: 16px;
      justify-content: center;
    }

    .face-card {
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.10);
      padding: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .face-card.parent { width: 220px; height: 220px; }
    .face-card.child  { width: 170px; height: 170px; }
    .face-card svg { width: 100%; height: auto; }

    .spinner { color: #bbb; font-size: 0.85rem; }

    button {
      padding: 8px 22px;
      font-size: 0.9rem;
      border: none;
      border-radius: 8px;
      background: #4a7c59;
      color: white;
      cursor: pointer;
    }
    button:hover  { background: #3b6347; }
    button:disabled { background: #aaa; cursor: default; }

    #btnChildren {
      padding: 8px 22px;
      font-size: 0.9rem;
    }

    #togglePoints {
      padding: 6px 16px;
      font-size: 0.8rem;
      border: 2px solid #4a7c59;
      border-radius: 8px;
      background: white;
      color: #4a7c59;
      cursor: pointer;
    }
    #togglePoints.active { background: #4a7c59; color: white; }

    .divider {
      width: 100%;
      max-width: 800px;
      border: none;
      border-top: 1px solid #ddd;
    }
  </style>
</head>
<body>
  <div style="display:flex;gap:12px;align-items:center;">
    <h1>Tender Face Generator</h1>
    <button id="togglePoints" onclick="togglePoints()">Show control points</button>
  </div>

  <div class="section">
    <div class="section-label">Parents</div>
    <div class="parents-row">
      <div class="parent-col">
        <div class="face-card parent" id="parent0"><span class="spinner">Loading...</span></div>
        <button onclick="newParent(0)">New face</button>
      </div>
      <div class="parent-col">
        <div class="face-card parent" id="parent1"><span class="spinner">Loading...</span></div>
        <button onclick="newParent(1)">New face</button>
      </div>
    </div>
  </div>

  <hr class="divider">

  <div class="section">
    <div class="section-label">Children</div>
    <div class="children-row">
      <div class="face-card child" id="child0"><span class="spinner">...</span></div>
      <div class="face-card child" id="child1"><span class="spinner">...</span></div>
      <div class="face-card child" id="child2"><span class="spinner">...</span></div>
      <div class="face-card child" id="child3"><span class="spinner">...</span></div>
    </div>
    <button id="btnChildren" onclick="newChildren()">New children</button>
  </div>

  <script>
    let pointsVisible = false;

    function togglePoints() {
      pointsVisible = !pointsVisible;
      const btn = document.getElementById('togglePoints');
      btn.textContent = pointsVisible ? 'Hide control points' : 'Show control points';
      btn.classList.toggle('active', pointsVisible);
      document.querySelectorAll('.ctrl-points').forEach(g => {
        g.style.display = pointsVisible ? '' : 'none';
      });
    }

    function applyPoints(root) {
      if (pointsVisible) {
        root.querySelectorAll('.ctrl-points').forEach(g => { g.style.display = ''; });
      }
    }

    function setLoading(ids) {
      ids.forEach(id => {
        document.getElementById(id).innerHTML = '<span class="spinner">...</span>';
      });
    }

    async function init() {
      setLoading(['parent0', 'parent1', 'child0', 'child1', 'child2', 'child3']);
      const res = await fetch('/parents');
      const svgs = await res.json();
      ['parent0', 'parent1'].forEach((id, i) => {
        const el = document.getElementById(id);
        el.innerHTML = svgs[i];
        applyPoints(el);
      });
      await fetchChildren();
    }

    async function newParent(idx) {
      setLoading([`parent${idx}`, 'child0', 'child1', 'child2', 'child3']);
      const res = await fetch(`/new_parent/${idx}`);
      const svg = await res.json();
      const el = document.getElementById(`parent${idx}`);
      el.innerHTML = svg;
      applyPoints(el);
      await fetchChildren();
    }

    async function newChildren() {
      setLoading(['child0', 'child1', 'child2', 'child3']);
      await fetchChildren();
    }

    async function fetchChildren() {
      const res = await fetch('/children');
      const svgs = await res.json();
      ['child0', 'child1', 'child2', 'child3'].forEach((id, i) => {
        const el = document.getElementById(id);
        el.innerHTML = svgs[i];
        applyPoints(el);
      });
    }

    init();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self._respond(200, 'text/html', HTML.encode())

        elif self.path == '/parents':
            parent_genomes[0] = Genome(num_genes=200)
            parent_genomes[1] = Genome(num_genes=200)
            svgs = [
                generate_face_svg(face_id='p0', genome=parent_genomes[0]),
                generate_face_svg(face_id='p1', genome=parent_genomes[1]),
            ]
            self._respond(200, 'application/json', json.dumps(svgs).encode())

        elif self.path == '/new_parent/0':
            parent_genomes[0] = Genome(num_genes=200)
            svg = generate_face_svg(face_id='p0', genome=parent_genomes[0])
            self._respond(200, 'application/json', json.dumps(svg).encode())

        elif self.path == '/new_parent/1':
            parent_genomes[1] = Genome(num_genes=200)
            svg = generate_face_svg(face_id='p1', genome=parent_genomes[1])
            self._respond(200, 'application/json', json.dumps(svg).encode())

        elif self.path == '/children':
            svgs = []
            for i in range(4):
                child_genome = Genome.make_child(parent_genomes[0], parent_genomes[1])
                svgs.append(generate_face_svg(face_id=f'c{i}', genome=child_genome))
            self._respond(200, 'application/json', json.dumps(svgs).encode())

        else:
            self._respond(404, 'text/plain', b'Not found')

    def _respond(self, code, content_type, body):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silence request logs


if __name__ == '__main__':
    server = HTTPServer(('localhost', PORT), Handler)
    url = f'http://localhost:{PORT}'
    print(f'Serving at {url}')
    webbrowser.open(url)
    server.serve_forever()
