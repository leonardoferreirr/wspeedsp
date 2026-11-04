// Celular 390x844: captura tela a tela rolando a página (fullPage falha com WebGL no modo móvel).
import { createRequire } from 'module';
const require = createRequire('/Users/Leonardo/dev/agencia-ia-escritorio/package.json');
const pw = require('playwright');
const [saida, rota] = [process.argv[2], process.argv[3] || '/'];
const BASE = process.env.BASE || 'http://127.0.0.1:4220';
const fs = await import('fs'); fs.mkdirSync(saida, { recursive: true });
const nav = await pw.chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const ctx = await nav.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true });
const pg = await ctx.newPage();
pg.on('pageerror', (e) => console.log('pageerror', e.message));
await pg.goto(BASE + rota, { waitUntil: 'networkidle' });
await pg.touchscreen.tap(5, 300);
await pg.waitForTimeout(1500);
const h = await pg.evaluate(() => document.documentElement.scrollHeight);
const passo = 780; let i = 0;
for (let y = 0; y < h; y += passo, i++) {
  await pg.evaluate((yy) => window.scrollTo(0, yy), y);
  await pg.waitForTimeout(900);
  await pg.screenshot({ path: `${saida}/cel${rota.replace(/\//g, '_')}-${String(i).padStart(2, '0')}.png` });
}
const larg = await pg.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
console.log(rota, 'altura', h, 'telas', i, 'largura', JSON.stringify(larg));
await nav.close();
