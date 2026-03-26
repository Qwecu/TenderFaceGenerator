import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


from TenderFace import generate_face_svg

PORT = 8765

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tender Face Generator</title>
  <style>
    body {
      font-family: sans-serif;
      background: #f5f5f0;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      gap: 24px;
    }
    h1 { margin: 0; font-size: 1.4rem; color: #333; }
    button {
      padding: 12px 32px;
      font-size: 1rem;
      border: none;
      border-radius: 8px;
      background: #4a7c59;
      color: white;
      cursor: pointer;
    }
    button:hover { background: #3b6347; }
    button:disabled { background: #aaa; cursor: default; }
    #togglePoints {
      padding: 8px 20px;
      font-size: 0.85rem;
      border: 2px solid #4a7c59;
      border-radius: 8px;
      background: white;
      color: #4a7c59;
      cursor: pointer;
    }
    #togglePoints.active {
      background: #4a7c59;
      color: white;
    }
    #grid {
      display: grid;
      grid-template-columns: repeat(2, 220px);
      gap: 20px;
    }
    .face-card {
      background: white;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      padding: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .face-card svg { width: 196px; height: auto; }
    .spinner { color: #888; font-size: 0.9rem; }
  </style>
</head>
<body>
  <h1>Tender Face Generator</h1>
  <div style="display:flex;gap:12px;align-items:center;">
    <button id="btn" onclick="generate()">Generate new random faces</button>
    <button id="togglePoints" onclick="togglePoints()">Show control points</button>
  </div>
  <div id="grid">
    <div class="face-card spinner">Loading...</div>
    <div class="face-card spinner">Loading...</div>
    <div class="face-card spinner">Loading...</div>
    <div class="face-card spinner">Loading...</div>
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

    async function generate() {
      const btn = document.getElementById('btn');
      const grid = document.getElementById('grid');
      btn.disabled = true;
      btn.textContent = 'Generating...';
      grid.querySelectorAll('.face-card').forEach(c => { c.innerHTML = '<span class="spinner">...</span>'; });

      const res = await fetch('/generate');
      const faces = await res.json();

      const cards = grid.querySelectorAll('.face-card');
      faces.forEach((svg, i) => { cards[i].innerHTML = svg; });
      if (pointsVisible) {
        document.querySelectorAll('.ctrl-points').forEach(g => { g.style.display = ''; });
      }

      btn.disabled = false;
      btn.textContent = 'Generate new random faces';
    }

    generate();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self._respond(200, 'text/html', HTML.encode())
        elif self.path.startswith('/generate'):
            faces = [generate_face_svg(face_id=str(i)) for i in range(4)]
            body = json.dumps(faces).encode()
            self._respond(200, 'application/json', body)
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
