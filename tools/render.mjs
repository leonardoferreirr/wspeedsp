// Renderiza as peças em PNG transparente pelo mesmo motor 3D do site.
// node tools/render.mjs <saida-dir> '<json com lista de {nome, tipo, dims, material, yaw, pitch, w, h}>'
import { createRequire } from 'module';
import http from 'http';
import fs from 'fs';
import path from 'path';
const require = createRequire('/Users/Leonardo/dev/agencia-ia-escritorio/package.json');
const pw = require('playwright');
const RAIZ = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const tipos = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };
const srv = http.createServer((q, r) => {
  const p = path.join(RAIZ, decodeURIComponent(q.url.split('?')[0]));
  if (!fs.existsSync(p)) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'content-type': tipos[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(r);
}).listen(0);
const porta = srv.address().port;
const [saida, lista] = [process.argv[2], JSON.parse(fs.readFileSync(process.argv[3], 'utf8'))];
fs.mkdirSync(saida, { recursive: true });
const nav = await pw.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const pg = await nav.newPage({ viewport: { width: 1000, height: 1000 } });
pg.on('console', (m) => { if (m.type() === 'error') console.log('console:', m.text()); });
pg.on('pageerror', (e) => console.log('pageerror:', e.message));
await pg.goto(`http://127.0.0.1:${porta}/tools/render.html`);
await pg.waitForFunction(() => window.pronto === true, null, { timeout: 30000 });
for (const it of lista) {
  const t0 = Date.now();
  const url = await pg.evaluate(([tipo, dims, o]) => window.renderizar(tipo, dims, o), [it.tipo, it.dims, it]);
  fs.writeFileSync(path.join(saida, it.nome + '.png'), Buffer.from(url.split(',')[1], 'base64'));
  console.log(it.nome, Date.now() - t0, 'ms');
}
await nav.close();
srv.close();
