#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

const outDir = path.join(process.cwd(), 'dist');
if (!fs.existsSync(outDir)) {
  fs.mkdirSync(outDir, { recursive: true });
}

const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FamilyAI Admin</title>
    <style>
      body { font-family: Helvetica, Arial, sans-serif; margin: 0; padding: 3rem; background: #0f172a; color: #e2e8f0; }
      header { max-width: 960px; margin: 0 auto 2rem; }
      section { background: #1e293b; border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; box-shadow: 0 10px 30px rgba(15,23,42,0.3); }
      h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
      h2 { font-size: 1.5rem; margin-top: 0; }
      code { background: rgba(148, 163, 184, 0.2); padding: 0.2rem 0.4rem; border-radius: 6px; }
      .grid { display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
      .card { background: #0f172a; border-radius: 10px; padding: 1rem; border: 1px solid rgba(148, 163, 184, 0.3); }
      .badge { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.75rem; background: #38bdf8; color: #082f49; }
      footer { text-align: center; font-size: 0.85rem; color: #94a3b8; margin-top: 2rem; }
    </style>
  </head>
  <body>
    <header>
      <h1>FamilyAI Control Center</h1>
      <p>Use the API endpoints exposed by <code>control-plane</code> to manage model catalogs, downloads, and inference routing. This UI stub can be replaced with a richer SPA.</p>
    </header>
    <section>
      <h2>Quick Links</h2>
      <div class="grid">
        <div class="card">
          <div class="badge">API</div>
          <h3>Model Catalog</h3>
          <p>GET <code>/models</code> for inventory, POST <code>/models/:id/download</code> to queue downloads.</p>
        </div>
        <div class="card">
          <div class="badge">Routing</div>
          <h3>Smart Selection</h3>
          <p>POST <code>/recommend</code> with task, context, and priorities to mirror OpenRouter-style selection.</p>
        </div>
        <div class="card">
          <div class="badge">Profiles</div>
          <h3>Activation</h3>
          <p>GET <code>/profiles</code> to inspect; POST <code>/profiles/:profile/activate</code> to switch.</p>
        </div>
      </div>
    </section>
    <footer>FamilyAI Admin Stub &mdash; Replace with full-featured panel when ready.</footer>
  </body>
</html>`;

fs.writeFileSync(path.join(outDir, 'index.html'), html);
